# Development Standards & Guidelines

## Overview

This document establishes development standards for the Core Engine project to ensure code quality, maintainability, and extensibility. These guidelines are especially important given the plugin-first architecture and AI-assisted development workflow.

## Core Principles

### 1. Plugin-First Development
- **Everything should be pluggable**: Features, integrations, AI agents, even core functionality
- **No vendor lock-in**: Users should be able to replace any component
- **Clear interfaces**: Well-defined contracts between components
- **Versioned APIs**: Maintain backward compatibility

### 2. Security by Design
- **No secrets in code**: Use environment variables and secret management
- **Least privilege**: Grant minimum necessary permissions
- **Input validation**: Validate all user inputs and external data
- **Audit trails**: Log security-relevant events

### 3. Maintainable Code
- **Clear naming**: Use descriptive names for variables, functions, and classes
- **Single responsibility**: Each function/class should have one clear purpose
- **Documentation**: Document complex logic and architectural decisions
- **Testing**: Write tests for all new functionality

## AI-Assisted Development Guidelines

### Working with AI Coding Assistants

#### ✅ Best Practices
- **Clear context**: Provide AI assistants with relevant context about the codebase
- **Iterative development**: Break complex tasks into smaller, manageable pieces
- **Code review**: Always review AI-generated code before merging
- **Document AI usage**: Note when AI assistance was used in commit messages

#### ❌ Anti-Patterns to Avoid
- **Blind copying**: Don't copy AI-generated code without understanding it
- **Secret exposure**: Never let AI assistants generate real secrets or credentials
- **Architecture drift**: Ensure AI-generated code follows project patterns
- **Artifact pollution**: Clean up AI development artifacts before committing

### Managing AI Development Artifacts

#### Artifacts to Clean Up
```bash
# MetaGPT/AI agent artifacts
.storage/
.MGXTools/
.MGXEnv.json
.timeline.json
**/task_*.json
**/agent_*.json

# Development artifacts
*.audit.txt
*_audit.txt
storage_*.txt
```

#### Pre-commit Checklist
- [ ] Remove all AI development artifacts
- [ ] No real secrets or credentials in code
- [ ] Code follows project patterns and conventions
- [ ] Tests added for new functionality
- [ ] Documentation updated if needed

## Code Standards

### Python Backend Standards

#### Code Style
```python
# Use type hints for all function signatures
async def create_user(user_data: UserCreate, db: AsyncSession) -> User:
    """Create a new user with validation."""

# Use Pydantic for data validation
class PluginManifest(BaseModel):
    name: str = Field(..., description="Plugin name")
    version: str = Field(..., regex=r"^\d+\.\d+\.\d+$")

# Proper error handling
try:
    result = await some_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

#### Database Patterns
```python
# Use async sessions properly
async with AsyncSessionLocal() as session:
    try:
        result = await session.execute(query)
        await session.commit()
        return result
    except Exception as e:
        await session.rollback()
        raise

# Use database migrations for schema changes
# Don't modify models directly in production
```

#### Plugin Development
```python
# All plugins must inherit from base classes
class MyPlugin(BasePlugin):
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration."""

    async def execute(self, context: ExecutionContext) -> Result:
        """Execute plugin functionality."""

# Use proper manifest schema
# manifest.yaml
name: my-plugin
version: 1.0.0
api_version: 1.0.0
category: integration
capabilities:
  - data_sync
  - oauth_auth
```

### TypeScript Frontend Standards

#### Component Structure
```typescript
// Use proper TypeScript interfaces
interface PluginComponentProps {
  pluginId: string;
  config: PluginConfig;
  onUpdate?: (data: any) => void;
}

// Functional components with proper typing
const PluginComponent: React.FC<PluginComponentProps> = ({
  pluginId,
  config,
  onUpdate
}) => {
  // Component logic
};

// Use custom hooks for logic separation
const usePluginData = (pluginId: string) => {
  const [data, setData] = useState<PluginData | null>(null);
  // Hook logic
  return { data, loading, error };
};
```

#### State Management
```typescript
// Use Zustand stores with proper typing
interface PluginStore {
  plugins: Record<string, PluginState>;
  loading: boolean;
  error: string | null;
}

const usePluginStore = create<PluginStore>((set, get) => ({
  plugins: {},
  loading: false,
  error: null,
  // Actions
  addPlugin: (plugin: Plugin) => set(state => ({
    plugins: { ...state.plugins, [plugin.id]: plugin }
  }))
}));
```

## Testing Standards

### Backend Testing
```python
# Test structure
tests/
├── unit/          # Unit tests for individual functions
├── integration/   # Integration tests for API endpoints
├── plugins/       # Plugin-specific tests
└── fixtures/      # Test data and fixtures

# Test naming convention
def test_create_user_with_valid_data():
    """Test user creation with valid input data."""

def test_plugin_loader_handles_invalid_manifest():
    """Test plugin loader error handling for invalid manifest."""

# Use pytest fixtures for common setup
@pytest.fixture
async def test_db():
    """Provide test database session."""

@pytest.fixture
def sample_plugin_manifest():
    """Provide sample plugin manifest for testing."""
```

### Frontend Testing
```typescript
// Component tests with React Testing Library
describe('PluginComponent', () => {
  it('renders plugin data correctly', () => {
    render(<PluginComponent pluginId="test" config={mockConfig} />);
    expect(screen.getByText('Plugin Name')).toBeInTheDocument();
  });

  it('handles plugin errors gracefully', async () => {
    // Test error handling
  });
});

// Integration tests for API calls
describe('Plugin API', () => {
  it('fetches plugin data successfully', async () => {
    // Test API integration
  });
});
```

## Security Standards

### Credential Management
```python
# ✅ Correct: Use environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")

# ❌ Wrong: Hardcoded credentials
DATABASE_URL = "postgresql://user:password@localhost/db"
```

### Input Validation
```python
# ✅ Validate all inputs
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

# ✅ Sanitize user inputs
def sanitize_filename(filename: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', filename)
```

### Plugin Security
```python
# Plugin permissions system
class PluginPermission(Enum):
    READ_USER_DATA = "read_user_data"
    WRITE_USER_DATA = "write_user_data"
    NETWORK_ACCESS = "network_access"
    FILE_SYSTEM_ACCESS = "file_system_access"

# Validate plugin permissions
def validate_plugin_permissions(plugin: Plugin, requested_action: str):
    required_permission = get_required_permission(requested_action)
    if required_permission not in plugin.permissions:
        raise PermissionDeniedError()
```

## Documentation Standards

### Code Documentation
```python
def complex_function(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """
    Brief description of what the function does.

    Args:
        param1: Description of parameter
        param2: Optional parameter description

    Returns:
        Dictionary containing the result

    Raises:
        ValueError: When param1 is invalid
        DatabaseError: When database operation fails

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["status"])
        success
    """
```

### API Documentation
- Use FastAPI's automatic OpenAPI generation
- Document all endpoints with proper examples
- Include error response examples
- Document authentication requirements

### Architecture Documentation
- Document major architectural decisions (ADRs)
- Keep plugin development guides updated
- Document deployment procedures
- Maintain troubleshooting guides

## Deployment Standards

### Environment Management
```yaml
# docker-compose.yml structure
services:
  backend:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      # Never hardcode secrets in docker-compose.yml

  postgres:
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

### Configuration Management
```python
# Use Pydantic settings for configuration
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    secret_key: str
    debug: bool = False

    class Config:
        case_sensitive = False
```

## Git Workflow

### Commit Standards
```bash
# Commit message format
type(scope): brief description

- feat: new feature
- fix: bug fix
- docs: documentation changes
- refactor: code refactoring
- test: adding tests
- chore: maintenance tasks

# Examples
feat(plugins): add OAuth2 support for GitHub integration
fix(auth): resolve token refresh issue
docs(api): update plugin development guide
```

### Branch Strategy
```
main                 # Production-ready code
├── develop         # Development integration branch
├── feature/xyz     # Feature development
├── hotfix/abc      # Critical bug fixes
└── release/v1.2.0  # Release preparation
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    hooks:
      - id: isort
  - repo: local
    hooks:
      - id: no-secrets
        name: Check for secrets
        entry: scripts/check-secrets.sh
```

## Monitoring and Observability

### Logging Standards
```python
import logging
import structlog

# Use structured logging
logger = structlog.get_logger(__name__)

# Log with context
logger.info(
    "Plugin executed successfully",
    plugin_id=plugin.id,
    user_id=user.id,
    duration_ms=duration,
    extra_context={"key": "value"}
)

# Error logging with context
logger.error(
    "Plugin execution failed",
    plugin_id=plugin.id,
    error=str(e),
    exc_info=True
)
```

### Performance Monitoring
```python
# Track plugin performance
@monitor_performance
async def execute_plugin(plugin: Plugin, context: Context):
    start_time = time.time()
    try:
        result = await plugin.execute(context)
        return result
    finally:
        duration = time.time() - start_time
        metrics.record_plugin_execution(plugin.id, duration)
```

## Plugin Development Guide

### Creating a New Plugin

1. **Create plugin directory structure**:
```
plugins/my-plugin/
├── manifest.yaml
├── __init__.py
├── main.py
├── requirements.txt
├── tests/
└── docs/
```

2. **Write manifest.yaml**:
```yaml
name: my-plugin
version: 1.0.0
api_version: 1.0.0
description: "Description of plugin functionality"
author: "Your Name"
category: integration
capabilities:
  - data_sync
  - oauth_auth
config_schema:
  type: object
  properties:
    api_url:
      type: string
      description: "API endpoint URL"
permissions:
  - network_access
  - read_user_data
```

3. **Implement plugin class**:
```python
from app.core.plugins import BasePlugin

class MyPlugin(BasePlugin):
    async def initialize(self, config: Dict[str, Any]) -> bool:
        self.api_url = config["api_url"]
        return True

    async def execute(self, context: ExecutionContext) -> Result:
        # Plugin implementation
        pass
```

4. **Write tests**:
```python
def test_plugin_initialization():
    plugin = MyPlugin()
    result = await plugin.initialize({"api_url": "https://api.example.com"})
    assert result is True
```

5. **Document the plugin**:
```markdown
# My Plugin

## Description
Brief description of what the plugin does.

## Configuration
Required configuration parameters.

## Usage
How to use the plugin.
```

This comprehensive guide ensures that the Core Engine project maintains high quality and extensibility as it grows.