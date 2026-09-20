"""
Where workflows are stored.

Two backends:
- Supabase (production): per-user rows in the `workflows` table. Survives redeploys.
- JSON files (local development, and when Supabase is not configured): backend/data/workflows.

Until now everything was written to JSON files on the container's disk, which Railway
replaces on every deploy, so saved workflows were lost.

Templates shipped with the repo stay on disk and are readable in both modes; saving one
writes a copy to the user's own storage rather than changing the shipped file.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.core.models import Workflow
from backend.utils.logger import get_logger

logger = get_logger(__name__)

WORKFLOWS_DIR = settings.workflows_dir
TABLE = "workflows"


def _parse_dates(data: Dict[str, Any]) -> Dict[str, Any]:
    """Turn ISO date strings into datetimes for the Workflow model."""
    for field in ("created_at", "updated_at", "deployed_at"):
        value = data.get(field)
        if isinstance(value, str):
            try:
                data[field] = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                data[field] = None
    return data


def _workflow_from_row(row: Dict[str, Any]) -> Optional[Workflow]:
    try:
        return Workflow(**_parse_dates({
            "id": str(row["id"]),
            "name": row["name"],
            "description": row.get("description"),
            "nodes": row.get("nodes") or [],
            "edges": row.get("edges") or [],
            "tags": row.get("tags") or [],
            "is_template": row.get("is_template", False),
            "is_deployed": row.get("is_deployed", False),
            "deployed_at": row.get("deployed_at"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
            "owner_id": str(row["user_id"]) if row.get("user_id") else None,
        }))
    except Exception as e:
        logger.error(f"Could not read workflow row {row.get('id')}: {e}")
        return None


def _row_from_workflow(workflow: Workflow, user_id: str) -> Dict[str, Any]:
    return {
        "id": workflow.id,
        "user_id": user_id,
        "name": workflow.name,
        "description": workflow.description,
        "nodes": [node.model_dump(mode="json") for node in workflow.nodes],
        "edges": [edge.model_dump(mode="json") for edge in workflow.edges],
        "tags": workflow.tags or [],
        "is_template": workflow.is_template,
        "is_deployed": workflow.is_deployed,
        "deployed_at": workflow.deployed_at.isoformat() if workflow.deployed_at else None,
        "updated_at": datetime.now().isoformat(),
    }


class WorkflowStore:
    """Reads and writes workflows for one user (or for local file mode when user_id is None)."""

    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self._supabase = None
        try:
            from backend.core.database import get_supabase_client
            self._supabase = get_supabase_client()
        except Exception as e:  # database module optional in some setups
            logger.debug(f"Supabase unavailable, using file storage: {e}")

    @property
    def uses_database(self) -> bool:
        return self._supabase is not None and self.user_id is not None

    # ------------------------------------------------------------------ read

    def load(self, workflow_id: str) -> Optional[Workflow]:
        if self.uses_database:
            try:
                result = (
                    self._supabase.table(TABLE).select("*")
                    .eq("id", workflow_id).eq("user_id", self.user_id).limit(1).execute()
                )
                if result.data:
                    return _workflow_from_row(result.data[0])
            except Exception as e:
                logger.error(f"Database read failed for workflow {workflow_id}: {e}")

        # Templates and pre-database workflows still live on disk
        workflow = self._load_file(workflow_id)
        if workflow and self.uses_database and workflow.owner_id and workflow.owner_id != self.user_id:
            if not workflow.is_template:
                return None  # someone else's leftover file
        return workflow

    def load_any(self, workflow_id: str) -> Optional[Workflow]:
        """
        Load a workflow whatever its owner, for endpoints the owner does not call:
        the deployed-workflow query API and webhook triggers.
        """
        if self._supabase is not None:
            try:
                result = self._supabase.table(TABLE).select("*").eq("id", workflow_id).limit(1).execute()
                if result.data:
                    return _workflow_from_row(result.data[0])
            except Exception as e:
                logger.error(f"Database read failed for workflow {workflow_id}: {e}")
        return self._load_file(workflow_id)

    def list(self) -> List[Workflow]:
        workflows: List[Workflow] = []
        seen: set = set()

        if self.uses_database:
            try:
                result = self._supabase.table(TABLE).select("*").eq("user_id", self.user_id).execute()
                for row in result.data or []:
                    workflow = _workflow_from_row(row)
                    if workflow:
                        workflows.append(workflow)
                        seen.add(workflow.id)
            except Exception as e:
                logger.error(f"Database list failed: {e}")

        # Bundled templates (and local files) stay visible
        for workflow in self._list_files():
            if workflow.id not in seen:
                if self.uses_database and not workflow.is_template:
                    continue  # a user's own workflows come from the database
                workflows.append(workflow)
        return workflows

    # ----------------------------------------------------------------- write

    def save(self, workflow: Workflow) -> None:
        if not workflow.id:
            raise ValueError("Workflow needs an id before saving")

        if self.uses_database:
            try:
                self._supabase.table(TABLE).upsert(
                    _row_from_workflow(workflow, self.user_id), on_conflict="id"
                ).execute()
                return
            except Exception as e:
                logger.error(f"Database save failed for workflow {workflow.id}, writing to disk: {e}")
        self._save_file(workflow)

    def delete(self, workflow_id: str) -> bool:
        deleted = False
        if self.uses_database:
            try:
                result = (
                    self._supabase.table(TABLE).delete()
                    .eq("id", workflow_id).eq("user_id", self.user_id).execute()
                )
                deleted = bool(result.data)
            except Exception as e:
                logger.error(f"Database delete failed for workflow {workflow_id}: {e}")

        path = self._path(workflow_id)
        if path.exists():
            path.unlink()
            deleted = True
        return deleted

    # ------------------------------------------------------------ file store

    @staticmethod
    def _path(workflow_id: str) -> Path:
        return WORKFLOWS_DIR / f"{workflow_id}.json"

    def _load_file(self, workflow_id: str) -> Optional[Workflow]:
        path = self._path(workflow_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = _parse_dates(json.load(f))
            return Workflow(**data)
        except Exception as e:
            logger.error(f"Error loading workflow {workflow_id} from disk: {e}")
            return None

    def _list_files(self) -> List[Workflow]:
        if not WORKFLOWS_DIR.exists():
            return []
        workflows = []
        for path in WORKFLOWS_DIR.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = _parse_dates(json.load(f))
                workflows.append(Workflow(**data))
            except Exception as e:
                logger.error(f"Error loading workflow file {path.name}: {e}")
        return workflows

    def _save_file(self, workflow: Workflow) -> None:
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        data = workflow.model_dump(mode="json")
        with open(self._path(workflow.id), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved workflow {workflow.id} to disk")


def get_workflow_store(user_id: Optional[str] = None) -> WorkflowStore:
    return WorkflowStore(user_id)
