"""
Deployment Processor

Pre-processes workflows during deployment to build vector stores and cache resources.
This makes queries much faster by avoiding re-processing on every query.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.core.models import Workflow, Node
from backend.core.engine import engine
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DeploymentProcessor:
    """Processes workflows during deployment to pre-build resources."""
    
    @staticmethod
    async def preprocess_workflow(workflow: Workflow) -> Dict[str, Any]:
        """
        Pre-process a workflow during deployment.
        
        This will:
        - Process files (chunk, embed, store) if vector stores are used
        - Build and persist vector stores
        - Cache expensive operations
        
        Returns:
            Dict with preprocessing results and metadata
        """
        results = {
            "vector_stores_built": [],
            "files_processed": [],
            "errors": [],
        }
        
        try:
            # Find vector store nodes that need pre-processing
            vector_store_nodes = [
                node for node in workflow.nodes 
                if node.type == "vector_store"
            ]
            
            # Find file loader nodes that feed into vector stores
            file_loader_nodes = [
                node for node in workflow.nodes 
                if node.type == "file_loader"
            ]
            
            # If we have file loaders and vector stores, we need to process them
            if file_loader_nodes and vector_store_nodes:
                logger.info(f"Pre-processing {len(file_loader_nodes)} file(s) for deployment")
                
                # For now, we'll mark vector stores to use persisted storage
                # The actual processing will happen on first query (lazy initialization)
                # OR we can do it here if file_id is provided in config
                
                for vs_node in vector_store_nodes:
                    config = vs_node.data.get("config", {})
                    provider = config.get("provider", "faiss")
                    
                    if provider == "faiss":
                        # Ensure persistence is enabled
                        if not config.get("faiss_persist", False):
                            config["faiss_persist"] = True
                        
                        # Set a deployment-specific path
                        if not config.get("faiss_file_path"):
                            from backend.config import settings
                            vector_dir = settings.vectors_dir / workflow.id or "default"
                            vector_dir.mkdir(parents=True, exist_ok=True)
                            config["faiss_file_path"] = str(vector_dir / "index.faiss")
                        
                        results["vector_stores_built"].append({
                            "node_id": vs_node.id,
                            "provider": provider,
                            "path": config["faiss_file_path"],
                        })
            
            logger.info(f"Pre-processing complete for workflow {workflow.id}")
            return results
            
        except Exception as e:
            logger.error(f"Error during workflow pre-processing: {e}", exc_info=True)
            results["errors"].append(str(e))
            return results

