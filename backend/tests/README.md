# Testing Guide

## Running Tests

### Backend Tests

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run tests matching a pattern
pytest -k "test_workflow"

# Run with verbose output
pytest -v

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Frontend Tests

```bash
# Run all tests
cd frontend
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Run in watch mode
npm test -- --watch
```

## Test Structure

```
backend/tests/
├── conftest.py          # Pytest configuration and fixtures
├── unit/                # Unit tests (fast, isolated)
│   ├── test_models.py
│   ├── test_node_registry.py
│   └── test_security.py
└── integration/         # Integration tests (slower, may require services)
    └── test_api_workflows.py

frontend/src/
└── test/
    ├── setup.ts         # Test setup and mocks
    └── utils.tsx        # Test utilities
```

## Writing Tests

### Backend Unit Test Example

```python
import pytest
from backend.core.models import Workflow

def test_create_workflow():
    workflow = Workflow(
        id="test-1",
        name="Test",
        nodes=[],
        edges=[]
    )
    assert workflow.id == "test-1"
```

### Frontend Component Test Example

```typescript
import { renderWithProviders, screen } from '@/test/utils';
import { MyComponent } from '@/components/MyComponent';

test('renders component', () => {
  renderWithProviders(<MyComponent />);
  expect(screen.getByText('Hello')).toBeInTheDocument();
});
```

## Test Markers

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow tests (skip in CI)
- `@pytest.mark.requires_api_key` - Tests requiring API keys
- `@pytest.mark.requires_network` - Tests requiring network

## CI/CD Integration

Tests should be run in CI/CD pipeline:
- On every pull request
- Before merging to main
- On scheduled basis

