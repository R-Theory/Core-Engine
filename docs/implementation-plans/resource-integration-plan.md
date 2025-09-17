# Resource Integration & Notion Sync Implementation Plan

## Purpose of This Document
This implementation plan defines the roadmap for bringing heterogeneous resources (Markdown, DOCX, PDF, TXT, external links) into the Core Engine while aligning with the platform's plugin-first architecture. It details how resource ingestion, storage, processing, and Notion synchronization should evolve across backend, frontend, and infrastructure workstreams.

- **Intended Location**: `docs/implementation-plans/resource-integration-plan.md`
- **Audience**: Core Engine contributors (backend, frontend, infra), product stakeholders, and future plugin authors
- **Related Docs**: `docs/prd.md`, `docs/system_design.md`, `docs/implementation-plans/plugin-system-document-engine.md`

---

## Final Goal & Vision

### Core Vision
Deliver a unified knowledge hub where users and AI agents can ingest, organize, and reference resources, with Core Engine serving as the source of truth and Notion acting as an optional reference view.

### Guiding Principles
- **Plugin-First Everything**: Extend existing parser, processor, and storage plugin abstractions for modularity.
- **User-Centric Knowledge Hub**: Ensure resources are easy to upload, organize, and retrieve across workflows.
- **Separation of Concerns**: Keep storage and advanced processing inside Core Engine while using Notion for presentation and lightweight collaboration.
- **Extensible by Design**: Provide clear extension points for future storage backends, AI enrichment, and UI modules.
- **Secure & Trustworthy**: Handle sensitive files with encryption, scoped access, and full auditability.

---

## Current State & Gaps

### Document Engine & Plugin System
- Parser, processor, and storage plugin abstractions exist with async processing and Celery background support.
- Plugin registry loads components via configuration, enabling modular behaviors.
- Document engine optimized for Markdown-focused flows and lacks a canonical resource domain model.

### Notion Integration
- Authentication, database/page retrieval, and basic CRUD operations already exist for Notion.
- Current integration is disconnected from document ingestion and lacks sync status tracking.

### Key Gaps
- Missing `Resource` entity that unifies content, metadata, storage locations, and sync state.
- Upload pipeline lacks persistence, per-user scoping, and user-visible progress.
- Notion integration does not reflect Core Engine resources or processing outcomes.
- Frontend lacks resource library views, upload UI, and plugin configuration screens.
- No embeddings or RAG hooks expose resources to AI workflows.

---

## Objectives & Success Criteria

### High-Level Objectives
1. Enable users to upload and manage mixed-format resources with rich metadata and status visibility.
2. Expose canonical resources to AI pipelines (RAG, embeddings) via structured APIs and plugin hooks.
3. Provide optional Notion sync for cataloging and visualization while keeping Core Engine as source of truth.

### User-Facing Success Criteria
- Drag-and-drop uploads with progress, error messaging, and retry options.
- Searchable resource library with filters for tags, type, project, and academic context.
- Configurable Notion mapping (database selection, property mapping, visibility) per user or workspace.
- Synced Notion links surface inside dashboards, detail views, and AI context panels.

### Technical Success Criteria
- Storage, parser, and processor plugins remain hot-swappable and configurable via plugin loader.
- Resource metadata indexed for search and future vector retrieval without rework.
- Notion sync resilient to rate limits, failures, and conflicts with observable telemetry.
- Background processing pipeline instrumented end-to-end with metrics and structured logging.

---

## Key Use Cases & User Journeys
1. **Upload & Organize**
   - User uploads Markdown, DOCX, TXT, or PDF.
   - System parses content, enriches metadata, stores canonical copy, and optionally creates a Notion page.
2. **Reference & Retrieval**
   - User or AI agent browses resource library, filters by tags/projects, opens detailed view or downloads raw file.
   - Notion link provides friendly context for sharing or collaboration.
3. **AI Contextualization**
   - AI workflows request resources via API, receiving processed content + metadata.
   - Future: embeddings provide semantic search for RAG flows.
4. **Task & Calendar Integration (Future)**
   - Notion tasks or calendar entries reference resources stored in Core Engine.

---

## Technical Architecture Overview
```
[Upload UI] -> [API Gateway] -> [Document Engine]
   |                                |         \
   |                                |          -> [Processor Plugins (AI enrichment, tagging)]
   v                                v
[Storage Plugin(s)] <---------- [Resource DB] ----> [Notion Sync Worker]
   |                                                     |
[Local/Cloud Storage]                            [Notion API]
```
- **Parser Plugins** convert raw files to normalized text & metadata.
- **Processor Plugins** enrich content (summaries, tags, embeddings later).
- **Storage Plugins** persist canonical content (local DB/files) and manage external references (Notion, cloud drives).
- **Notion** serves as an external reference layer; Core Engine remains source of truth.

---

## Data Model & Storage Design
### Resource Entity (Core DB)
- `id`, `owner_id`
- `title`, `description`
- `content_uri` (storage location), `content_hash`
- `file_type`, `mime_type`, `size`
- `metadata` JSONB (tags, parser info, academic/project context, external links)
- `processing_status`, `processing_errors`
- `notion_reference` JSONB (page ID, database ID, last sync timestamp, sync status)
- Audit fields (`created_at`, `updated_at`)

### Versioning & Relationships
- Version table linking `resource_id` → version number, `content_uri`, `created_at`.
- Many-to-many relationship with tags table or JSON tags for initial iteration.
- Join tables to associate resources with GitHub repos, courses, tasks, or calendar events.

### Storage Considerations
- Default persistence in Postgres for metadata + optional file system/S3 for binaries.
- Support external references (Google Docs link) without storing binary by marking `storage_type = external`.
- Streaming uploads and configurable size limits for large files.
- Encryption at rest for stored binaries; hashed filenames to prevent collisions.

---

## API & Service Layer Plan
### Backend Endpoints (FastAPI)
- `POST /api/v1/resources/upload` – Multipart upload, returns processing task ID + preliminary metadata.
- `GET /api/v1/resources/:id` – Fetch resource metadata, storage info, Notion status.
- `GET /api/v1/resources` – List/filter resources (pagination, tags, type, search query).
- `GET /api/v1/resources/:id/content` – Stream canonical content if user has permission.
- `POST /api/v1/resources/:id/sync-notion` – Manual sync trigger and configuration override.
- `GET /api/v1/resources/search` – Keyword/semantic search (stub until embeddings ready).

### Service Layer Responsibilities
- Document engine orchestrates parser/processor/storage operations via Celery tasks.
- Upload flow: temporary storage → parser selection → metadata extraction → processor hooks → storage commit → Notion sync queue.
- Notion sync worker reads from queue, calls Notion API, updates `notion_reference` fields.
- Storage plugin interfaces extended for metadata-only operations (e.g., linking to external docs).

### Access Control & Security
- Per-user scoping enforced at API, DB, and storage layers.
- Role-based permissions for shared resources (future).
- Audit all operations (upload, download, sync) with user ID and timestamps.

---

## Phased Execution Plan

### Phase 0: Foundations & Prerequisites (Week 0.5)
**Difficulty:** 3/10 – Configuration and scaffolding

- [ ] Validate database migrations tooling and create baseline migration for resource tables.
- [ ] Finalize configuration schemas (Notion tokens, storage plugin priorities, feature flags).
- [ ] Ensure secrets management supports per-user Notion credentials and encryption keys.
- [ ] Update developer onboarding docs for new environment variables and plugin expectations.

### Phase 1: Core Resource Ingestion Pipeline (Week 1)
**Difficulty:** 5/10 – Establish canonical resource model and processing flow

- [ ] Create `Resource` SQLAlchemy models, Alembic migrations, and repository layer.
- [ ] Implement temporary upload storage (filesystem or object store) with cleanup policies.
- [ ] Extend document engine to enqueue parsing/processing tasks upon upload submission.
- [ ] Enhance parser plugins (Markdown, TXT, PDF, DOCX) for metadata extraction; provide graceful fallbacks for unsupported types.
- [ ] Persist parsed content & metadata; expose processing status via API/WebSocket events.

### Phase 2: Storage Plugins & Persistence (Week 2)
**Difficulty:** 6/10 – Durable storage and plugin configurability

- [ ] Implement default storage plugin persisting metadata in Postgres and binaries in filesystem/S3.
- [ ] Add plugin configuration schema to allow per-user/workspace storage plugin selection and prioritization.
- [ ] Build admin/CLI tools for listing registered storage plugins and verifying health.
- [ ] Provide management APIs for enabling/disabling storage targets and setting priorities.

### Phase 3: Notion Integration & Sync (Week 3)
**Difficulty:** 6/10 – External sync orchestration

- [ ] Define Notion database schema recommendations (Title, File Type, Tags, Source, Last Synced, Status).
- [ ] Implement Notion sync worker that reads resource updates and pushes to Notion pages.
- [ ] Create mapping layer translating resource metadata to Notion properties with configurable templates.
- [ ] Handle rate limits and retries with exponential backoff; surface errors in UI & logs.
- [ ] Track sync status, timestamps, and Notion page IDs in resource records.

### Phase 4: Frontend Resource Library & Dashboard Surfacing (Week 4)
**Difficulty:** 7/10 – UX and configuration polish

- [ ] Build resource upload modal/component with drag-drop, progress, and error states.
- [ ] Implement resource listing page with filters, search, tag chips, and sort options.
- [ ] Show Notion sync state, provide manual re-sync button, and open Notion page in new tab.
- [ ] Integrate resource summaries into dashboard widgets and AI context panels.
- [ ] Add settings UI for selecting Notion database, configuring property mapping, and enabling storage plugins.

### Phase 5: AI/RAG Enablement Hooks (Week 5+)
**Difficulty:** 7/10 – ML integration groundwork

- [ ] Generate embeddings per resource via pluggable embedding provider (OpenAI, local models, etc.).
- [ ] Store embeddings in vector index (e.g., PGVector) tied to resource metadata.
- [ ] Expose API endpoints for AI workflows to fetch resources by semantic similarity or metadata filters.
- [ ] Provide context packaging (chunking strategy, metadata filters) for downstream AI agents.

### Phase 6: Polishing, Observability & Documentation (Ongoing)
**Difficulty:** 4/10 – Hardening and rollout

- [ ] Instrument pipeline with metrics (processing duration, failure rates, Notion sync latency).
- [ ] Add user notifications for failed uploads or sync issues (email, in-app alerts).
- [ ] Document plugin interfaces, Notion setup guide, troubleshooting steps, and sample configurations.
- [ ] Conduct final QA, usability testing, and prepare release notes.

---

## Detailed Workstreams Per Phase
### Backend
- SQLAlchemy models, migrations, repository/service classes, Celery tasks, and plugin interfaces.
- Parser/processor/storage plugin implementations + registry configuration.
- Notion sync worker logic with error handling, retries, and logging.

### Frontend
- Upload wizard, resource list/detail components, Notion configuration forms.
- State management updates (React Query/Zustand) for resource fetching & sync status.
- Dashboard widgets showing resource highlights, quick links, and AI context prompts.

### DevOps & Infrastructure
- Storage provisioning (volume mounts, S3 buckets), backup policies, and monitoring.
- Celery worker scaling strategies for processing + sync tasks.
- Secrets management for Notion tokens and encryption keys.
- Observability dashboards (Grafana/Prometheus) for pipeline health.

### Testing & QA
- Unit tests for parsers with sample fixtures (Markdown, DOCX, PDF).
- Integration tests for upload → process → store → sync flow.
- Contract tests for Notion API interactions using sandbox or mocked responses.
- Frontend component tests for upload UI, list filtering, and settings forms.
- Load testing for concurrent uploads and Notion sync throughput.

---

## Notion Integration Strategy
### Content Mapping
- Core fields → Notion properties (Title, Tags, File Type, Source URL, Last Synced).
- Include Core Engine resource link + optional public share link.
- Store summary/description in Notion for quick scanning.

### Database Setup & Configuration
- Recommend dedicated Notion database per workspace (configurable via settings).
- Provide setup wizard guiding users to create/select database, map properties, and authorize integration.
- Allow configuration of Notion template for newly created pages (e.g., default sections for notes, tasks).

### Sync Directionality & Conflict Resolution
- MVP: One-way sync (Core Engine → Notion).
- Future: Poll or subscribe to Notion changes (webhooks) to sync status/tags back.
- Conflict policy: Core Engine remains source of truth; Notion edits flagged for manual resolution.

### Reliability & Observability
- Queue sync jobs in Celery with exponential backoff on failure.
- Cache Notion metadata to minimize API calls; respect rate limits.
- Provide admin dashboard for sync status, failures, and retry controls.
- Log structured events for monitoring and audit trails.

---

## Security, Privacy & Compliance
- Encrypt stored files at rest; use signed URLs or authenticated streams for downloads.
- Restrict access to resources by user/role; support sharing scopes in future iterations.
- Store Notion access tokens securely (hashed/encrypted) with per-user scoping and revocation flow.
- Provide audit logs for uploads, downloads, Notion sync actions, and configuration changes.
- Consider redaction tools for sensitive data prior to AI enrichment or external sync.
- Ensure GDPR/CCPA compliance for data deletion requests and consent management.

---

## Testing & Validation Plan
- **Automated Tests**
  - Parser fixtures covering Markdown, DOCX, PDF, TXT with edge cases.
  - Storage plugin mocks verifying CRUD, versioning, and error handling.
  - Notion sync tests using recorded responses or sandbox accounts.
  - API contract tests ensuring upload and retrieval endpoints behave consistently.
- **Manual QA**
  - End-to-end upload flows with various file sizes and formats.
  - Notion sync verification (page creation, property mapping, error scenarios).
  - Frontend UX validation (accessibility, responsiveness, localization readiness).
- **Load & Resilience**
  - Stress test large upload batches; confirm queue scaling and retry behavior.
  - Simulate Notion downtime to verify retry and backoff strategies.
  - Chaos testing for storage failures (e.g., S3 unavailable) and ensure graceful degradation.

---

## Rollout & Migration Strategy
- Gate new resource UI and Notion sync behind feature flags.
- Beta test with internal users to gather feedback on UX, performance, and reliability.
- Provide migration scripts or CLI tools if existing documents need ingestion into new `Resource` model.
- Publish documentation, setup wizard, and video walkthrough for onboarding.
- Establish rollback plan (disable feature flag, revert migrations if necessary).

---

## Risks, Dependencies & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Notion API rate limits | Sync delays, user frustration | Queue jobs, cache metadata, allow manual retry |
| Complex file formats (DOCX/PDF) | Parsing errors or data loss | Use battle-tested libraries, fallback to attachments, log failures |
| Storage plugin misconfiguration | Data loss or unavailability | Validation tests, health checks, warning prompts in UI |
| User confusion on Notion mapping | Poor adoption | Provide setup wizard, templates, docs, and contextual help |
| Large files / storage costs | Infrastructure strain | Enforce size limits, streaming uploads, optional offloading to external storage |
| Security breaches | Loss of trust | Encrypt data, enforce access controls, regular security audits |
| Dependency on Celery workers | Pipeline stalls if workers fail | Implement health checks, auto-scaling, monitoring, and alerting |

Dependencies: Stable parser libraries, Celery workers, Notion credentials, storage volumes/S3, vector database (Phase 5).

---

## Success Metrics

### Performance Targets
- Upload request acknowledgment: < 2 seconds before handing off to background processing.
- Notion sync completion: < 45 seconds for typical documents (<5 MB) under normal rate limits.
- Vector embedding generation: < 30 seconds per resource once Phase 5 is enabled.

### Reliability Targets
- ≥ 99% successful processing jobs (excluding user-cancelled uploads).
- Automatic retry covers ≥ 90% of transient Notion failures without manual intervention.
- Celery worker availability monitored with alerts firing within 2 minutes of downtime.

### User Experience Targets
- Upload UX earns ≥ 4/5 satisfaction in beta surveys.
- Resource library search returns results in < 700 ms for 95th percentile queries.
- Configuration wizard completion (storage + Notion) succeeds for ≥ 90% of users on first attempt.

---

## Future Extensions & Open Questions
### Future Extensions
- Support Google Docs and other cloud sources via connectors (OAuth + API ingestion).
- Build dataset export pipeline for fine-tuning or offline training.
- Introduce marketplace for community storage/processor plugins with discoverability.
- Integrate Notion tasks/calendar bidirectionally for life-management workflows.
- Add automation rules (e.g., auto-tag resources based on Notion properties or GitHub repo metadata).

### Open Questions
- Preferred default storage backend (Postgres vs. filesystem)?
- Do we need per-resource sharing controls in MVP or can it wait?
- How to surface AI-generated summaries within Notion without overwriting user content?
- What retention policies should govern large binaries and old versions?
- How should we handle multi-user workspaces with shared Notion databases?

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
- **Resource**: Canonical representation of uploaded or linked knowledge asset.
- **Parser Plugin**: Component that normalizes raw files into structured text + metadata.
- **Processor Plugin**: Component that enriches resources (summaries, tags, embeddings).
- **Storage Plugin**: Component that persists content/metadata or links to external stores.
- **Notion Reference Layer**: Notion database/pages representing resources for user-friendly viewing and organization.
- **RAG**: Retrieval-Augmented Generation; AI technique using external knowledge bases for context.

