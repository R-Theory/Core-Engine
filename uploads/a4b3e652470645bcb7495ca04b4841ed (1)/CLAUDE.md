# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Core Engine MVP - an AI-powered learning and project management platform for university computer science students. It provides a modular, extensible system for course management, AI agent orchestration, plugin integrations, and workflow automation.

## Development Commands

### Backend Development
```bash
cd workspace/backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations  
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run linting
flake8 app/
black app/ --check

# Format code
black app/
```

### Frontend Development
```bash
cd workspace/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run linting
npm run lint
```

### Docker Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild services
docker-compose up --build
```

### Testing
```bash
# Backend unit tests
cd workspace/backend && pytest

# Frontend unit tests  
cd workspace/frontend && npm test

# System integration test
python workspace/scripts/test_system.py
```

## Architecture Overview

### Tech Stack
- **Backend**: FastAPI (Python 3.11+) with async/await
- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS
- **Database**: PostgreSQL 15 with async SQLAlchemy 2.0
- **Cache/Queue**: Redis 7 with Celery for background tasks
- **Containerization**: Docker with docker-compose

### Core Components

1. **Plugin System** (`app/core/plugin_loader.py`)
   - Dynamic plugin loading with YAML manifests
   - Sandboxed execution with Docker containers
   - OAuth integration support for external services

2. **AI Agent Framework** (`app/core/agent_registry.py`)
   - Unified interface for MetaGPT, Claude, Perplexity
   - Chain-of-responsibility execution pattern
   - Cost tracking and usage monitoring

3. **Course Management** (`app/models/course.py`)
   - "Live Map" visualization system
   - Canvas LMS integration for automatic sync
   - Assignment and resource relationship mapping

4. **Workflow Engine** (`app/tasks/`)
   - Visual workflow builder with conditional logic
   - Scheduled execution with Celery beat
   - Error handling with retry mechanisms

### Directory Structure

```
workspace/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core system components  
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   ├── tasks/         # Background tasks
│   │   └── plugins/       # Plugin implementations
│   ├── alembic/           # Database migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/           # Next.js app router
│       ├── components/    # React components
│       ├── stores/        # Zustand state stores
│       └── lib/           # Utilities and API client
├── docs/                  # Documentation
└── scripts/               # Development scripts
```

## Data Models

### Key Relationships
- **User** → **Courses** (1:many)
- **Course** → **Assignments** (1:many)  
- **Course** → **Topics** (1:many)
- **Assignment** → **Resources** (many:many)
- **User** → **Workflows** (1:many)
- **Workflow** → **WorkflowExecutions** (1:many)

### Plugin System
- Plugins define capabilities in `manifest.yaml`
- Sandboxed execution with Docker containers
- OAuth credentials encrypted in `user_plugin_configs` table

### AI Agents
- Standardized interface in `BaseAgent` class
- Request/response tracking in `agent_interactions` table
- Cost and token usage monitoring

## External Integrations

### Canvas LMS (`plugins/canvas-integration/`)
- OAuth 2.0 authentication flow
- Course and assignment synchronization
- Webhook support for real-time updates

### GitHub (`plugins/github-integration/`)
- Repository monitoring and analysis
- Commit activity tracking
- Pull request and issue integration

### Google Drive (`plugins/google-drive/`)
- File synchronization and metadata extraction
- Document access and sharing
- Resource association with courses

## Security Considerations

### Authentication
- JWT tokens with refresh rotation
- OAuth 2.0 for external services
- Row-level security policies in PostgreSQL

### Plugin Security
- Docker-based sandboxing
- Network isolation by default
- Granular permission system
- Resource limits (CPU, memory, storage)

### Data Protection
- AES-256 encryption for sensitive data
- TLS 1.3 for all communications
- Input validation and sanitization

## Performance Features

### Database Optimization
- Connection pooling with SQLAlchemy
- Optimized indexes for common queries
- Full-text search with PostgreSQL GIN indexes

### Caching Strategy
- Redis caching for API responses
- Application-level caching for AI results
- Background processing with Celery

### Async Processing
- FastAPI async/await throughout
- Background tasks for long-running operations
- WebSocket support for real-time updates

## Development Guidelines

### Code Style
- **Backend**: Follow PEP 8, use Black formatter
- **Frontend**: ESLint + Prettier configuration
- **Database**: Use Alembic for migrations
- **API**: OpenAPI/Swagger documentation

### Testing Strategy
- Unit tests with pytest (backend) and Jest (frontend)
- Integration tests for plugin system
- AI agent mocking for consistent testing
- System-level integration tests

### Plugin Development
1. Create plugin directory in `backend/plugins/`
2. Define capabilities in `manifest.yaml`
3. Implement `BasePlugin` interface
4. Add OAuth configuration if needed
5. Write tests for plugin functionality

### AI Agent Integration
1. Extend `BaseAgent` class
2. Implement required abstract methods
3. Add cost tracking and error handling
4. Register agent in `agent_registry.py`

## Deployment

### Development
```bash
docker-compose up -d
# Access frontend at http://localhost:3000
# Access API docs at http://localhost:8000/docs
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
- Set API keys for AI services (OpenAI, Anthropic, MetaGPT)
- Configure OAuth credentials for external services
- Database and Redis connection strings
- Security keys and encryption settings

## Common Tasks

### Adding New Plugin
1. Create plugin directory structure
2. Implement manifest.yaml with capabilities
3. Create plugin class extending BasePlugin
4. Add OAuth flow if needed
5. Write tests and documentation

### Adding New AI Agent
1. Create agent class extending BaseAgent
2. Implement required capabilities
3. Add to agent registry
4. Configure API credentials
5. Add cost tracking

### Database Changes
1. Create Alembic migration: `alembic revision -m "description"`
2. Implement upgrade/downgrade functions
3. Test migration on development data
4. Apply: `alembic upgrade head`

### Adding New API Endpoint
1. Create route in appropriate `app/api/` module
2. Add request/response models with Pydantic
3. Implement business logic in `app/services/`
4. Add authentication/authorization if needed
5. Write tests for endpoint

## Monitoring and Observability

### Health Checks
- `/health` endpoint for application status
- Database and Redis connectivity checks
- Plugin system health monitoring

### Logging
- Structured JSON logging
- AI interaction tracking
- Plugin execution logging
- Error tracking and alerting

### Metrics
- API response times and error rates
- AI agent usage and costs
- Plugin execution metrics
- Database query performance