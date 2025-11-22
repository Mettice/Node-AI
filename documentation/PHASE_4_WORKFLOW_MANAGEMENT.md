# Phase 4: Workflow Management

**Duration:** Week 8  
**Status:** 🔄 Not Started  
**Prerequisites:** [Phase 3: Complete RAG Pipeline](./PHASE_3_COMPLETE_RAG.md)

---

## 🎯 Goals

- Save and load workflows
- Workflow templates
- Version control
- Workflow sharing

---

## 📋 Tasks

### Backend: Workflow CRUD

#### 1. Workflow API (`backend/api/workflows.py`)

- [ ] `POST /api/v1/workflows` - Create workflow
  - Accept workflow JSON
  - Validate workflow structure
  - Generate workflow ID
  - Save to database
  - Return workflow with ID

- [ ] `GET /api/v1/workflows` - List workflows
  - Return list of workflows (metadata only)
  - Support pagination
  - Support filtering (by name, tags, etc.)
  - Support sorting (by date, name, etc.)

- [ ] `GET /api/v1/workflows/{workflow_id}` - Get workflow
  - Return full workflow JSON
  - Include version information
  - Return 404 if not found

- [ ] `PUT /api/v1/workflows/{workflow_id}` - Update workflow
  - Update workflow data
  - Create new version (if versioning enabled)
  - Validate workflow structure
  - Return updated workflow

- [ ] `DELETE /api/v1/workflows/{workflow_id}` - Delete workflow
  - Soft delete (mark as deleted)
  - Or hard delete (remove from database)
  - Delete associated executions (optional)
  - Return success status

#### 2. Workflow Service (`backend/services/workflow_service.py`)

- [ ] Validation:
  - Validate workflow structure
  - Check node types exist
  - Validate edges (no cycles, valid connections)
  - Check required node configurations

- [ ] Versioning:
  - Create version on update
  - Track version history
  - Support version comparison
  - Support rollback

- [ ] Template management:
  - Mark workflows as templates
  - List available templates
  - Clone templates to new workflows

#### 3. Database Integration

- [ ] Migrate from file storage to SQLite:
  - Create database schema
  - Migrate existing workflows
  - Set up database connection

- [ ] Workflow schema:
  ```sql
  CREATE TABLE workflows (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      description TEXT,
      workflow_json TEXT NOT NULL,
      tags TEXT,  -- JSON array
      is_template BOOLEAN DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```

- [ ] Execution history schema:
  ```sql
  CREATE TABLE executions (
      id TEXT PRIMARY KEY,
      workflow_id TEXT NOT NULL,
      status TEXT NOT NULL,
      started_at TIMESTAMP,
      completed_at TIMESTAMP,
      total_cost REAL,
      execution_json TEXT,  -- Full execution data
      FOREIGN KEY (workflow_id) REFERENCES workflows(id)
  );
  ```

- [ ] Version schema:
  ```sql
  CREATE TABLE workflow_versions (
      id TEXT PRIMARY KEY,
      workflow_id TEXT NOT NULL,
      version_number INTEGER NOT NULL,
      workflow_json TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (workflow_id) REFERENCES workflows(id),
      UNIQUE(workflow_id, version_number)
  );
  ```

- [ ] Indexes for performance:
  - Index on `workflow_id` in executions
  - Index on `created_at` in workflows
  - Index on `is_template` in workflows

---

### Backend: Version Control

#### 1. Version Management

- [ ] Create workflow versions:
  - Auto-create version on update
  - Increment version number
  - Store full workflow JSON
  - Track version metadata

- [ ] Tag releases:
  - Tag specific versions
  - Store tag names
  - Support semantic versioning

- [ ] Rollback to previous version:
  - Restore workflow from version
  - Create new version from rollback
  - Preserve version history

- [ ] Compare versions:
  - Diff two versions
  - Highlight changes
  - Show node/edge differences

#### 2. Version API

- [ ] `GET /api/v1/workflows/{workflow_id}/versions`
  - List all versions
  - Return version metadata
  - Support pagination

- [ ] `GET /api/v1/workflows/{workflow_id}/versions/{version_number}`
  - Get specific version
  - Return full workflow JSON

- [ ] `POST /api/v1/workflows/{workflow_id}/versions`
  - Create new version manually
  - Tag version (optional)

- [ ] `POST /api/v1/workflows/{workflow_id}/rollback/{version_number}`
  - Rollback to specific version
  - Create new version from rollback

- [ ] `GET /api/v1/workflows/{workflow_id}/versions/compare`
  - Compare two versions
  - Return diff JSON

---

### Frontend: Workflow Management

#### 1. Workflow List (`frontend/src/components/Workflows/WorkflowList.tsx`)

- [ ] List all workflows:
  - Display workflow cards
  - Show workflow name, description, tags
  - Show last modified date
  - Show execution count (optional)

- [ ] Search/filter:
  - Search by name or description
  - Filter by tags
  - Filter by template status
  - Sort by date, name, etc.

- [ ] Create new workflow:
  - "New Workflow" button
  - Create blank workflow
  - Or create from template

- [ ] Delete workflow:
  - Delete button on each card
  - Confirmation dialog
  - Remove from list

#### 2. Workflow Save/Load

- [ ] Save button:
  - Save current workflow
  - Show save dialog (name, description, tags)
  - Auto-save option (debounced)
  - Show save status

- [ ] Load dropdown:
  - List saved workflows
  - Search in dropdown
  - Load workflow on selection
  - Confirm if unsaved changes

- [ ] Auto-save (optional):
  - Save periodically
  - Save on workflow change
  - Show auto-save indicator

#### 3. Workflow Templates

- [ ] Template gallery:
  - Display available templates
  - Show template preview
  - Show template description
  - Show usage count (optional)

- [ ] Pre-built workflows:
  - Simple RAG
  - Document Q&A
  - Multi-document search
  - Custom templates

- [ ] One-click template use:
  - Click to use template
  - Create new workflow from template
  - Load template on canvas

#### 4. Version Control UI

- [ ] Version history:
  - Display version list
  - Show version number, date, description
  - Highlight current version

- [ ] Version comparison:
  - Select two versions
  - Show side-by-side comparison
  - Highlight differences

- [ ] Rollback button:
  - Rollback to selected version
  - Confirm rollback action
  - Show rollback status

---

## ✅ Deliverables Checklist

- [ ] Can save workflows
- [ ] Can load workflows
- [ ] Can list workflows
- [ ] Can delete workflows
- [ ] Version control working
- [ ] Can rollback to previous version
- [ ] Can compare versions
- [ ] Workflow templates available
- [ ] Can create workflow from template
- [ ] Database migration complete
- [ ] All API endpoints working

---

## 🗄️ Database Schema

### Workflows Table
```sql
CREATE TABLE workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    workflow_json TEXT NOT NULL,
    tags TEXT,  -- JSON array of strings
    is_template BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflows_created_at ON workflows(created_at);
CREATE INDEX idx_workflows_is_template ON workflows(is_template);
```

### Workflow Versions Table
```sql
CREATE TABLE workflow_versions (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    workflow_json TEXT NOT NULL,
    description TEXT,
    tag TEXT,  -- e.g., "v1.0.0", "production"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    UNIQUE(workflow_id, version_number)
);

CREATE INDEX idx_versions_workflow_id ON workflow_versions(workflow_id);
```

### Executions Table (Enhanced)
```sql
CREATE TABLE executions (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    workflow_version INTEGER,  -- Version used for execution
    status TEXT NOT NULL,  -- pending, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_cost REAL,
    execution_json TEXT,  -- Full execution data
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

CREATE INDEX idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX idx_executions_started_at ON executions(started_at);
```

---

## 🧪 API Examples

### Create Workflow
```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Simple RAG",
    "description": "Basi
      "nodes":c RAG workflow",
    "workflow": { [...],
      "edges": [...]
    },
    "tags": ["rag", "basic"]
  }'
```

### List Workflows
```bash
curl http://localhost:8000/api/v1/workflows?page=1&limit=10
```

### Get Workflow
```bash
curl http://localhost:8000/api/v1/workflows/{workflow_id}
```

### Update Workflow
```bash
curl -X PUT http://localhost:8000/api/v1/workflows/{workflow_id} \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated RAG",
    "workflow": {...}
  }'
```

### Get Versions
```bash
curl http://localhost:8000/api/v1/workflows/{workflow_id}/versions
```

### Rollback Version
```bash
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/rollback/2
```

---

## 📝 Notes

- Use SQLite for MVP, can upgrade to PostgreSQL later
- Implement soft deletes for workflows
- Consider workflow sharing/permissions (future)
- Template system should be extensible
- Version comparison should be visual

---

## 🔗 Related Files

- `backend/api/workflows.py` - Workflow API endpoints
- `backend/services/workflow_service.py` - Workflow business logic
- `backend/storage/database.py` - Database connection and models
- `frontend/src/components/Workflows/` - Workflow management UI

---

## ➡️ Next Phase

Once Phase 4 is complete, proceed to [Phase 5: Polish & Deploy](./PHASE_5_POLISH_DEPLOY.md)

