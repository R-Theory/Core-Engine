# Core Engine MVP

**The Extensible AI-Powered Learning Operating System**

*Built on the philosophy of modularity, extensibility, and intelligent automation*

## Vision & Philosophy

Core Engine represents a paradigm shift in educational technology - a **plugin-first, AI-native platform** that grows with its users. Our core beliefs:

**🔌 Modularity by Design**: Every feature is a plugin. Every integration is extensible. No vendor lock-in, ever.

**🧠 Intelligence at the Core**: AI isn't bolted on - it's fundamental. Context-aware, personalized, and continuously learning.

**🛠️ Extensibility First**: Built for hackers, by hackers. If you can dream it, you can plugin it.

**🎯 User-Centric**: Technology should adapt to users, not the other way around. Personalized experiences that evolve.

## What Makes Core Engine Different

Unlike monolithic LMS platforms, Core Engine is:
- **Plugin-Native**: Everything is a plugin - integrations, AI providers, even core features
- **Context-Aware**: Learns your patterns, preferences, and goals to provide intelligent assistance
- **Infinitely Extensible**: Write custom plugins for any service, any workflow, any idea
- **AI-First**: Multiple AI providers working together, each optimized for different tasks
- **Student-Owned**: Your data, your plugins, your customizations - complete control

## Features

### 🎓 Course Management
- **Live Map Visualization**: Interactive course topology with topics, assignments, and resources
- **Canvas Integration**: Automatic synchronization of courses, assignments, and grades
- **Progress Tracking**: Visual progress indicators and completion analytics

### 🧠 AI Context & Personalization System
- **Contextual Memory**: Learns your preferences, goals, and working patterns over time
- **Multi-Provider Intelligence**: OpenAI GPT-4, Anthropic Claude, and more working in harmony
- **Personalized Prompts**: AI responses tailored to your learning style and current projects
- **Conversation History**: Maintains context across sessions for deeper understanding
- **Privacy-First**: All personal data encrypted and stored locally - your context stays yours

### 🤖 Extensible AI Framework  
- **Provider Agnostic**: Switch between AI providers seamlessly based on task requirements
- **Capability Mapping**: Route different tasks to the AI best suited for the job
- **Mock Responses**: Development-friendly testing without burning API credits
- **Usage Analytics**: Track AI usage patterns and optimize costs

### 🔌 Plugin-First Architecture
- **Everything is a Plugin**: Core features, integrations, even AI providers are plugins
- **Hot-Swappable**: Enable/disable features without restarts
- **Manifest-Driven**: Simple YAML configuration for complex integrations
- **Secure by Default**: Sandboxed execution with granular permissions
- **Community Extensible**: Plugin marketplace for sharing custom integrations

### 🔐 Modular Credential Management
- **Provider-Based System**: Each service gets its own secure credential management
- **Encrypted Storage**: AES-256 encryption for all sensitive data
- **Per-User Isolation**: Credentials are isolated per user with zero cross-contamination
- **Extensible Providers**: Add new services with simple configuration objects
- **Connection Testing**: Validate credentials before saving

### 📚 Resource Management
- **Central Vault**: Unified storage for files, links, notes, and code repositories
- **Smart Tagging**: Automatic and manual tagging with contextual associations
- **Full-Text Search**: Advanced search across all resource types
- **AI Summaries**: Automatic content summarization and insights

### ⚡ Workflow Automation
- **Visual Builder**: Drag-and-drop workflow creation interface
- **Scheduled Execution**: Cron-like scheduling for automated tasks
- **Error Handling**: Robust error handling with retry mechanisms
- **Template Library**: Pre-built workflows for common academic tasks

### 🎨 Modern UI/UX
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Real-Time Updates**: Live data synchronization and notifications
- **Dark Mode**: Support for light and dark themes
- **Accessibility**: WCAG 2.1 AA compliant interface
- **Component-Driven**: Reusable UI components that grow with the platform

## Core Engine Philosophy: The Plugin Principle

**"If it can be a plugin, it should be a plugin"**

This isn't just a technical decision - it's our fundamental philosophy. Core Engine treats everything as composable, swappable modules:

### Why Plugin-Everything?

1. **Zero Vendor Lock-in**: Don't like our Canvas integration? Write your own. Prefer a different AI provider? Swap it out.

2. **Infinite Extensibility**: Need integration with your university's custom system? Create a plugin. Want to automate your specific workflow? Plugin it.

3. **Community Innovation**: The best features come from users who know their own needs. Our plugin system makes innovation accessible to everyone.

4. **Future-Proof Architecture**: New services, APIs, and tools emerge constantly. Plugins let us adapt instantly without core changes.

5. **Granular Control**: Enable only what you need. Your Core Engine instance is uniquely yours.

### The Technical Implementation

- **Dynamic Loading**: Plugins are discovered and loaded at runtime
- **Isolation**: Each plugin runs in its own secure context
- **API-First**: Consistent interfaces regardless of plugin complexity  
- **Declarative Configuration**: YAML manifests describe capabilities and requirements
- **Dependency Management**: Automatic resolution of plugin dependencies

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework with async support
- **PostgreSQL**: Primary database with full-text search capabilities
- **Redis**: Caching and message queue for background tasks
- **Celery**: Distributed task queue for workflow execution
- **SQLAlchemy**: Async ORM with connection pooling

### Frontend
- **Next.js 13+**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Zustand**: Lightweight state management
- **TanStack Query**: Server state management

### Infrastructure
- **Docker**: Containerization for all services
- **Docker Compose**: Local development orchestration
- **Nginx**: Reverse proxy and load balancer
- **Kubernetes**: Production deployment (optional)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd core-engine-mvp
```

### 2. Environment Setup
```bash
# Copy environment template
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit environment variables
# Set API keys for AI agents and external services
```

### 3. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Default Login
- **Email**: admin@coreengine.dev
- **Password**: admin123

## Development Setup

### Backend Development
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Configuration

### Environment Variables

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/core_engine

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# AI Agents
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
METAGPT_API_KEY=your-metagpt-key

# External APIs
CANVAS_CLIENT_ID=your-canvas-client-id
CANVAS_CLIENT_SECRET=your-canvas-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret
```

## Plugin Development

### Creating a Plugin

1. **Create Plugin Directory**
```bash
mkdir backend/plugins/my-plugin
cd backend/plugins/my-plugin
```

2. **Create Manifest File** (`manifest.yaml`)
```yaml
name: "my-plugin"
version: "1.0.0"
description: "My custom plugin"
author: "Your Name"
category: "custom"

capabilities:
  - "my_action"

config_schema:
  api_key:
    type: "string"
    required: true
    secret: true

permissions:
  - "network:external"
  - "storage:read"
```

3. **Create Plugin Class** (`main.py`)
```python
from app.core.plugin_loader import BasePlugin

class PluginClass(BasePlugin):
    async def my_action(self, **params):
        # Your plugin logic here
        return {"success": True, "data": "Hello from my plugin!"}
```

### Plugin API Reference

See `/docs/plugin-development.md` for complete plugin development guide.

## Workflow Examples

### Example 1: Weekly Assignment Summary
```yaml
name: "Weekly Assignment Summary"
description: "Generate weekly summary of upcoming assignments"

steps:
  - name: "fetch_assignments"
    type: "plugin_action"
    plugin: "canvas-integration"
    action: "get_assignments"
    params:
      due_within_days: 7
      
  - name: "analyze_assignments"
    type: "ai_agent"
    agent: "claude"
    capability: "text_analysis"
    input_data:
      text: "{steps.fetch_assignments.output}"
      analysis_type: "summary"
      
  - name: "send_notification"
    type: "system_action"
    action: "create_notification"
    params:
      title: "Weekly Assignment Summary"
      content: "{steps.analyze_assignments.output.summary}"
```

### Example 2: Code Review Automation
```yaml
name: "Code Review Assistant"
description: "Analyze GitHub commits and provide feedback"

steps:
  - name: "fetch_recent_commits"
    type: "plugin_action"
    plugin: "github-integration"
    action: "get_commits"
    params:
      since: "24h"
      
  - name: "analyze_code"
    type: "ai_agent"
    agent: "metagpt"
    capability: "code_analysis"
    input_data:
      code: "{steps.fetch_recent_commits.output}"
      
  - name: "create_review_summary"
    type: "ai_agent"
    agent: "claude"
    capability: "text_analysis"
    input_data:
      text: "{steps.analyze_code.output}"
      analysis_type: "code_review"
```

## API Documentation

### Authentication
```bash
# Login
POST /api/v1/auth/login
{
  "username": "user@example.com",
  "password": "password"
}

# Register
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "username": "username",
  "password": "password",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Courses
```bash
# Get all courses
GET /api/v1/courses

# Create course
POST /api/v1/courses
{
  "name": "Computer Science 101",
  "code": "CS101",
  "semester": "Fall 2024",
  "instructor": "Dr. Smith"
}

# Get course live map
GET /api/v1/courses/{course_id}/live-map
```

### AI Agents
```bash
# List available agents
GET /api/v1/agents

# Interact with agent
POST /api/v1/agents/{agent_name}/interact
{
  "capability": "text_analysis",
  "input_data": {
    "text": "Analyze this content...",
    "analysis_type": "summary"
  }
}
```

For complete API documentation, visit http://localhost:8000/docs when running the application.

## Deployment

### Production Deployment

1. **Build Docker Images**
```bash
# Build backend
docker build -t core-engine/backend:latest ./backend

# Build frontend
docker build -t core-engine/frontend:latest ./frontend
```

2. **Deploy with Docker Compose**
```bash
# Use production overrides with base compose
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

3. **Deploy with Kubernetes**
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

### Environment-Specific Configuration

- **Development**: Use `docker-compose.yml`
- **Staging**: Use `docker-compose.staging.yml`
- **Production**: Use `docker-compose.prod.yml`

## Monitoring and Observability

### Health Checks
- **Backend**: http://localhost:8000/health
- **Database**: Built-in PostgreSQL health checks
- **Redis**: Built-in Redis health checks

### Metrics
- **Prometheus**: Application metrics collection
- **Grafana**: Metrics visualization
- **Logs**: Structured logging with JSON format

### Alerting
- **System Health**: Database and Redis connectivity
- **Performance**: API response times and error rates
- **AI Costs**: Usage tracking and budget alerts

## Security

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **OAuth 2.0**: Integration with external services
- **Role-Based Access**: User permission management

### Data Protection
- **Encryption**: AES-256 encryption for sensitive data
- **TLS**: All communications encrypted in transit
- **Input Validation**: Comprehensive input sanitization

### Plugin Security
- **Sandboxing**: Docker-based plugin isolation
- **Permissions**: Granular permission system
- **Code Signing**: Plugin authenticity verification

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Standards
- **Backend**: Follow PEP 8 and use Black formatter
- **Frontend**: Use ESLint and Prettier
- **Tests**: Maintain >80% code coverage
- **Documentation**: Update docs for new features

### Issue Reporting
- Use GitHub Issues for bug reports and feature requests
- Include detailed reproduction steps
- Provide environment information

## Support

### Documentation
- **API Docs**: http://localhost:8000/docs
- **Plugin Guide**: `/docs/plugin-development.md`
- **Workflow Examples**: `/docs/workflow-examples.md`

### Community
- **GitHub Discussions**: Ask questions and share ideas
- **Discord**: Real-time community chat
- **Email**: support@coreengine.dev

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Roadmap

### Phase 1 (Current)
- ✅ Core infrastructure and authentication
- ✅ Plugin system with Canvas, GitHub, Google Drive
- ✅ AI agent framework with MetaGPT, Claude
- ✅ Course management and live map
- ✅ Resource management and search
- ✅ Workflow automation engine

### Phase 2 (Next 3 months)
- 📱 Mobile application (React Native)
- 🔍 Advanced analytics and insights
- 🤝 Collaboration features
- 📊 Enhanced visualizations
- 🔐 Advanced security features

### Phase 3 (Next 6 months)
- 🏢 Multi-tenant architecture
- 🌐 Plugin marketplace
- 🎯 Predictive analytics
- 🔄 Advanced workflow features
- 📈 Performance optimizations

---

**Built with ❤️ for students, by students.**
