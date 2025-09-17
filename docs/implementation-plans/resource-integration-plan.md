# Resource Integration & Notion Sync Implementation Plan

## Purpose of This Document
This implementation plan describes how Core Engine will evolve into a unified resource hub that ingests heterogeneous files, enriches them through the document engine, and exposes them to both humans and AI systems while optionally surfacing references in Notion. It is intended for contributors across backend, frontend, infra, and product who need a shared roadmap and vocabulary for the resource pipeline. This document lives in `docs/implementation-plans/resource-integration-plan.md` and complements `docs/prd.md`, `docs/system_design.md`, and the `plugin-system-document-engine` implementation plan.

---

## Final Goal & Vision

### Core Vision
Create a **modular resource pipeline** that enables the Core Engine to:
- Accept and normalize diverse resource types (Markdown, TXT, DOCX, PDF, etc.)
- Persist authoritative copies locally while projecting references into Notion for organization
- Serve curated context to AI workflows (RAG, embeddings, assistants)
- Remain extensible through the existing plugin architecture so storage, processing, and sync behaviors are swappable

### Guiding Principles
- **Plugin-First Everything**: Resource ingestion, processing, storage, and sync are all implemented as plugins with clear contracts.
- **User-Centric Knowledge Hub**: Provide a cohesive experience for users—and AI agents—to discover, organize, and act on their resources.
- **Separation of Concerns**: Core Engine owns canonical data; Notion provides a friendly reference layer and dashboard surface.
- **Secure & Trustworthy**: Treat uploaded content as sensitive by default (encryption, auditability, scoped access).
- **Extensible by Design**: Every major component exposes interfaces for future storage backends, AI enrichments, and UI extensions.

### Scope Clarifications & Non-Goals
- **Notion is not the source of truth**: It mirrors key metadata and links but Core Engine maintains canonical storage and history.
- **Initial focus is on file-based resources**: Google Docs and other cloud sources remain future connectors.
- **AI training/export pipelines are deferred**: Hooks will exist for embeddings/RAG, but full training dataset workflows ship later.
- **Per-resource collaboration controls**: Scoped sharing is future work; MVP assumes per-user scoping with workspace-level configuration.

---

## Success Criteria

### User Perspective
- ✅ Drag-and-drop upload flows with clear progress, retry, and error messaging
- ✅ Searchable resource library with filters for tags, type, projects, and academic context
- ✅ Notion references displayed in dashboards and detail views with one-click open
- ✅ Configurable Notion mapping (database selection, property mapping, visibility) per user or workspace

### Frontend Experience
- ✅ Resource upload modal/component integrated into dashboard and resource library
- ✅ Resource list/detail pages with status indicators and manual re-sync controls
- ✅ Settings UI for plugin configuration (storage priorities, Notion database, embeddings toggle)
- ✅ Non-blocking UX—background processing updates via WebSockets/toasts

### Backend & Infrastructure
- ✅ Unified `Resource` domain model with versioning and metadata indexing
- ✅ Parser/processor/storage plugins remain hot-swappable and discoverable via registry
- ✅ Background pipeline observable (metrics, logs, alerts) with resilient retry behavior
- ✅ Storage of binaries supports encryption at rest and streaming access for large files

### Notion Integration
- ✅ One-way sync from Core Engine → Notion with mapping to recommended database schema
- ✅ Sync worker handles rate limits, retries, and error surfacing
- ✅ Audit trail tracks when/what was synced, with manual re-sync capability
- ✅ Future bidirectional sync points identified and gated behind feature flags

---

## Base Environment

### Current Codebase State
- **Architecture**: FastAPI backend, Next.js frontend, PostgreSQL, Redis, Celery workers
- **Integration Engine**: Extensible system already supporting Canvas, GitHub, Notion
- **UI System**: Glassmorphism-inspired interface with configurable dashboard and settings modules
- **Infrastructure**: Docker Compose for local dev with separate backend/frontend services

### Existing Capabilities
- User authentication, profiles, and integration management flows
- Plugin-style document engine abstractions (parser, processor, storage) albeit optimized for Markdown
- Background task orchestration through Celery + Redis
- Notion OAuth + API helpers for listing databases/pages

### Technical Foundation Snapshot
```
backend/
├── app/core/document_engine.py      # Orchestrates parser/processor/storage plugins
├── app/core/plugin_system.py        # Plugin registry & loader
├── app/integrations/notion/         # Notion auth + API wrappers
├── app/api/v1/                      # REST endpoints
└── app/tasks/                       # Celery tasks for async work

frontend/
├── src/components/                  # Shared UI primitives
├── src/app/(dashboard|settings)/    # Primary surfaces for new UI
└── src/lib/api/                     # Client helpers for REST endpoints
```

### Known Constraints & Dependencies
- Celery workers must remain healthy for ingestion and sync; add monitoring early
- Notion API enforces rate limits—batching and caching are essential
- Storage volume/S3 credentials determine feasible file size limits
- Vector database (e.g., PGVector) needed before Phase 5

---

## Key Use Cases & User Journeys
1. **Upload & Organize**
   - User uploads Markdown, DOCX, TXT, or PDF file(s)
   - Pipeline parses content, extracts metadata, persists canonical copy, enqueues optional Notion sync
2. **Reference & Retrieval**
   - User or AI agent browses the resource library, filters by tags/project, opens viewer or downloads raw file
   - Notion link offers friendly view for sharing and organization
3. **AI Contextualization**
   - AI workflows request resources through API; receive structured content + metadata for prompts or RAG
   - Embeddings and chunking prepared for semantic search (Phase 5)
4. **Operational Oversight**
   - Admin/dev monitors pipeline health, reviews sync failures, adjusts plugin configuration

---

## Architecture Overview
```
[Upload UI] -> [API Gateway] -> [Document Engine]
   |                                |         \
   |                                |          -> [Processor Plugins (enrichment, tagging)]
   v                                v
[Storage Plugin(s)] <---------- [Resource DB] ----> [Notion Sync Worker]
   |                                                     |
[Local/Cloud Storage]                            [Notion API]
```
- **Parser Plugins** normalize raw files into structured text + metadata
- **Processor Plugins** add enrichments (summaries, tags, embeddings later)
- **Storage Plugins** persist canonical content and manage pointers to external systems
- **Notion Sync Worker** mirrors key metadata into Notion database/pages for reference

---

## Data Model & Storage Design

### Resource Entity (PostgreSQL)
- `id`, `owner_id`, `workspace_id`
- `title`, `description`, `tags`
- `content_uri`, `content_hash`, `storage_type`
- `file_type`, `mime_type`, `size`
- `metadata` JSONB (parser info, course/project associations, external links)
- `processing_status`, `processing_errors`
- `notion_reference` JSONB (database ID, page ID, sync status, timestamps)
- Audit fields: `created_at`, `updated_at`, `deleted_at`

### Versioning & Relationships
- `resource_versions` table storing historical blobs + metadata for reprocessing
- Join tables for linking resources to GitHub repos, academic terms, tasks, or calendar events
- Tagging strategy: JSON for v1, upgrade to normalized tables when analytics require it

### Storage Considerations
- Default metadata in Postgres + binaries in filesystem/S3 with encryption at rest
- Streaming uploads with configurable size limits and automatic cleanup of temp files
- External-only resources (e.g., Google Docs links) flagged with `storage_type = external`
- Signed URLs or authenticated streaming for downloads to avoid exposing raw paths

---

## API & Service Layer Plan

### Backend Endpoints (FastAPI)
- `POST /api/v1/resources/upload` – Multipart upload → returns processing task ID & prelim metadata
- `GET /api/v1/resources` – Paginated list with filters (tags, type, status, search)
- `GET /api/v1/resources/{id}` – Metadata, storage info, Notion sync status, version history
- `GET /api/v1/resources/{id}/content` – Stream canonical content if authorized
- `POST /api/v1/resources/{id}/sync-notion` – Manual sync trigger / override configuration
- `GET /api/v1/resources/search` – Keyword (Phase 3) + semantic search (Phase 5)

### Service Responsibilities
- Upload flow: temp storage → parser selection → metadata extraction → processor hooks → storage commit → optional Notion sync queue
- Celery tasks handle heavy parsing, processing, and Notion sync to keep API responsive
- Storage plugin interfaces extend to support metadata-only operations and health checks
- Access control enforced at API, DB, and storage layers with auditing on every operation

---

## Implementation Plan

### Phase 0: Foundations & Prerequisites (Week 0)
**Difficulty: 3/10 – Setup groundwork**
- [ ] Confirm Alembic migration strategy and create baseline migration for resource tables
- [ ] Finalize configuration schemas (feature flags, Notion credentials, storage priorities)
- [ ] Document new environment variables + secrets handling for contributors
- [ ] Establish monitoring/alerting requirements for Celery workers and Notion API usage

### Phase 1: Core Resource Ingestion Pipeline (Weeks 1–2)
**Difficulty: 5/10 – Core domain modeling & ingestion**
- **Backend**
  - [ ] Implement `Resource` SQLAlchemy models, repositories, and migrations
  - [ ] Create upload endpoint storing files in temp location and enqueuing processing task
  - [ ] Enhance parser plugins (Markdown, TXT, PDF, DOCX) with metadata extraction + graceful fallbacks
  - [ ] Persist parsed content & metadata; expose processing status via polling/WebSocket events
- **Frontend**
  - [ ] Build upload modal with drag-drop, progress bar, and error states
  - [ ] Wire dashboard CTA to new upload flow
- **Infra**
  - [ ] Configure storage volume/S3 bucket for resource binaries with encryption
  - [ ] Add scheduled cleanup for temp uploads

### Phase 2: Storage Plugins & Persistence (Weeks 3–4)
**Difficulty: 6/10 – Storage abstraction + configuration**
- **Backend**
  - [ ] Implement default storage plugin persisting metadata in Postgres + binaries in filesystem/S3
  - [ ] Add plugin configuration schema for per-user/workspace storage priorities
  - [ ] Provide admin/CLI tooling to inspect registered storage plugins & health
- **Frontend**
  - [ ] Extend settings UI for enabling/disabling storage plugins and ordering priorities
- **Infra**
  - [ ] Add health checks + alerts for storage backends (disk usage, S3 errors)

### Phase 3: Notion Integration & Sync (Weeks 5–6)
**Difficulty: 7/10 – External sync & resiliency**
- **Backend**
  - [ ] Define Notion database template + property mappings
  - [ ] Implement Notion sync worker (Celery) with exponential backoff + structured logging
  - [ ] Track sync metadata on resources (status, timestamps, errors)
- **Frontend**
  - [ ] Build settings wizard to authorize Notion, pick database, and map properties
  - [ ] Surface Notion sync status + manual re-sync button in resource detail
- **Infra**
  - [ ] Monitor Notion API usage + rate limits; configure alert thresholds

### Phase 4: Resource Library & Dashboard Surfacing (Weeks 7–8)
**Difficulty: 6/10 – UX & discoverability**
- **Backend**
  - [ ] Implement filtering/search endpoints (tags, type, text query)
  - [ ] Provide aggregation endpoints for dashboard widgets (recent uploads, failed syncs)
- **Frontend**
  - [ ] Create resource library page with filters, list cards/table, status chips
  - [ ] Integrate resource summaries into dashboard widgets + AI context sidebar
  - [ ] Show Notion link badges and quick actions (open, re-sync, copy share link)
- **Infra**
  - [ ] Ensure CDN or caching strategy for frequently accessed files if size warrants

### Phase 5: AI/RAG Enablement Hooks (Weeks 9–10)
**Difficulty: 7/10 – ML integrations**
- **Backend**
  - [ ] Generate embeddings via pluggable provider; store in PGVector or chosen index
  - [ ] Implement chunking + metadata strategy for RAG-friendly retrieval
  - [ ] Expose semantic search endpoint for AI workflows
- **Frontend**
  - [ ] Add toggle in settings to enable embeddings per workspace (with quota info)
  - [ ] Surface AI-ready metadata (embedding status) in resource detail view
- **Infra**
  - [ ] Provision vector database extensions (PGVector) and monitor usage

### Phase 6: Polishing, Observability & Documentation (Weeks 11–12)
**Difficulty: 4/10 – Hardening & rollout**
- **Backend/Infra**
  - [ ] Instrument metrics (processing duration, failure rate, Notion latency) + Grafana dashboards
  - [ ] Implement audit log export + retention policies
  - [ ] Add automated backup/restore procedures for resource binaries and metadata
- **Frontend**
  - [ ] Provide user notifications (toasts/email) for failed uploads or sync issues
  - [ ] Finalize documentation pages, walkthrough videos, and troubleshooting FAQ
- **QA**
  - [ ] Conduct accessibility review, cross-browser testing, and load testing for concurrent uploads

---

## Detailed Workstreams
- **Backend**: Domain modeling, parser/processor/storage plugins, Celery tasks, Notion sync worker, API endpoints, telemetry
- **Frontend**: Upload UX, resource library, Notion configuration flows, dashboard widgets, status indicators
- **DevOps & Infrastructure**: Storage provisioning, secrets management, worker scaling, monitoring/alerting, backup strategy
- **Testing & QA**: Unit/integration/e2e tests, contract tests against Notion sandbox, load & chaos exercises

---

## Notion Integration Strategy

### Content Mapping
- Map core fields → Notion properties (Title, Tags, File Type, Source URL, Last Synced, Status, Summary)
- Include Core Engine deep link + optional public share link
- Support configurable templates for consistent page layout

### Database Setup & Configuration
- Recommend dedicated Notion database per workspace; allow selection via settings wizard
- Store mapping in secure config tied to user/workspace credentials
- Provide preview of sample record before enabling sync

### Sync Directionality & Conflict Handling
- MVP: One-way sync (Core Engine → Notion)
- Plan for future webhook/polling to ingest Notion edits (status, tags) without overwriting user content
- Flag conflicts (Notion edits detected) and require manual reconciliation via UI

### Reliability & Observability
- Queue sync jobs in Celery with exponential backoff and dead-letter queue for repeated failures
- Cache Notion metadata to minimize API calls; respect rate limits with adaptive throttling
- Provide admin dashboard for sync status, failure counts, and retry actions
- Log structured events for auditing and analytics

---

## Security, Privacy & Compliance
- Encrypt binaries at rest and in transit; use signed URLs or token-protected streams
- Enforce per-user/workspace authorization for all resource operations; audit every access
- Store Notion OAuth tokens encrypted with rotation + revocation flows
- Support user-driven deletion (GDPR/CCPA) with cascading removal of binaries and Notion references
- Provide optional redaction tools or warnings before syncing sensitive data to external systems

---

## Testing & Validation Plan
- **Automated Tests**
  - Parser fixtures for Markdown, DOCX, PDF, TXT (happy path + edge cases)
  - Storage plugin unit tests + health check coverage
  - Integration tests covering upload → process → store → Notion sync
  - Contract tests leveraging Notion sandbox or VCR fixtures
- **Manual QA**
  - End-to-end upload scenarios across browsers/devices
  - Notion sync verification (page creation, property mapping, error handling)
  - Frontend UX validation (accessibility, localization readiness, offline states)
- **Load & Resilience**
  - Stress tests for concurrent uploads and large files
  - Chaos simulations for Notion downtime, storage failures, and worker restarts
  - Benchmark semantic search latency once embeddings are enabled

---

## Rollout & Migration Strategy
- Gate major features behind feature flags (upload pipeline, Notion sync, embeddings)
- Run internal beta with power users; collect feedback on UX, reliability, performance
- Provide migration tooling if existing documents must be ported into new `Resource` model
- Publish setup wizard, documentation, and video walkthrough prior to GA
- Define rollback steps (disable flags, revert migrations, clear queues) for emergency scenarios

---

## Risks, Dependencies & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Notion API rate limits or outages | Sync delays, inconsistent references | Queue jobs, cache metadata, expose manual retry, alert on sustained failures |
| Complex file formats (DOCX/PDF) | Parsing errors, partial ingestion | Use mature libraries, maintain fallback to attachments, log + notify users |
| Storage misconfiguration | Data loss/unavailability | Health checks, automated backups, configuration validation in UI |
| Large files/storage cost | Infrastructure strain | Enforce size limits, streaming uploads, lifecycle policies for old versions |
| Security breach or token leakage | Loss of trust/compliance risk | Encrypt tokens, rotate secrets, audit access, add anomaly detection |
| Celery worker downtime | Pipeline stalls & backlog | Auto-scaling, health probes, alerting, ability to requeue tasks |
| Vector database unavailability | AI features degraded | Graceful degradation to keyword search, monitor index health |

Dependencies: Stable parser libraries, Celery + Redis infrastructure, Notion credentials, storage backends (filesystem/S3), vector database (Phase 5), observability stack.

---

## Future Extensions & Open Questions

### Future Extensions
- Connectors for Google Docs, Slides, Sheets, and other cloud sources
- Dataset export pipeline for fine-tuning or offline training workflows
- Marketplace for community-built storage/processor plugins with discoverability in UI
- Bidirectional Notion sync for tasks, calendar events, and status updates
- Automation rules (e.g., auto-tag resources based on Notion properties or GitHub repo metadata)

### Open Questions
- Preferred default storage backend for self-hosted deployments (Postgres vs. filesystem vs. S3)?
- Do we require granular sharing controls in MVP or can workspace scope suffice?
- How should AI-generated summaries appear in Notion without overwriting manual edits?
- What retention/lifecycle policies govern large binaries and historical versions?
- How do we support multi-user workspaces mapping to shared Notion databases securely?

---

## Appendices

### Suggested Notion Database Template
| Property | Type | Description |
|----------|------|-------------|
| Name | Title | Resource title |
| Tags | Multi-select | Topics, projects, academic courses |
| File Type | Select | Markdown, PDF, DOCX, TXT, External |
| Source URL | URL | Link back to Core Engine resource detail |
| Last Synced | Date | Timestamp of most recent sync |
| Status | Select | Ingested, Processing, Sync Failed, Archived |
| Summary | Rich text | Short description or AI-generated summary |

### Example API Payloads
- **Upload Response**
  ```json
  {
    "resource_id": "res_123",
    "status": "processing",
    "upload_task_id": "task_abc",
    "notion_sync": {
      "enabled": true,
      "status": "pending"
    }
  }
  ```
- **Resource Detail**
  ```json
  {
    "id": "res_123",
    "title": "Linear Algebra Notes",
    "file_type": "markdown",
    "tags": ["math", "university"],
    "metadata": {
      "course": "Math 221",
      "notion_page_id": "abcd1234",
      "content_hash": "..."
    },
    "processing_status": "completed",
    "notion_reference": {
      "page_id": "abcd1234",
      "database_id": "xyz987",
      "last_synced_at": "2024-05-01T12:34:56Z",
      "status": "ok"
    }
  }
  ```

### Glossary
- **Resource**: Canonical representation of an uploaded or linked knowledge asset.
- **Parser Plugin**: Component that normalizes raw files into structured text + metadata.
- **Processor Plugin**: Component that enriches resources (summaries, tags, embeddings).
- **Storage Plugin**: Component that persists content/metadata or links to external stores.
- **Notion Reference Layer**: Notion database/pages representing resources for user-friendly viewing and organization.
- **RAG**: Retrieval-Augmented Generation; AI technique using external knowledge bases for context.

