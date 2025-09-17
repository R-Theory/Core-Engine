# Resource Integration & Notion Sync Implementation Plan

## 1. Document Overview
- **Purpose**: Define a phased roadmap for integrating heterogeneous resources (Markdown, text, DOCX, PDFs, etc.) into Core Engine while leveraging Notion as a reference-friendly layer.
- **Scope**: Backend ingestion pipeline, storage plugins, Notion sync, frontend resource experiences, and AI enablement hooks.
- **Intended Location**: `docs/implementation-plans/resource-integration-plan.md`.
- **Audience**: Core Engine contributors (backend, frontend, infra), product stakeholders, and future plugin authors.
- **Related Documents**: `docs/prd.md`, `docs/system_design.md`, `docs/implementation-plans/plugin-system-document-engine.md`.

---

## 2. Vision & Guiding Principles
1. **Plugin-First Everything**: Extend the existing plugin system so resource ingestion, processing, and storage remain modular and swappable.
2. **User-Centric Knowledge Hub**: Provide a cohesive place for users (and AI agents) to store, reference, and act upon their knowledge assets.
3. **Separation of Concerns**: Treat Notion as a "reference/view layer," while Core Engine handles authoritative storage and advanced processing.
4. **Extensible by Design**: Create clear interfaces for future storage backends, processors (AI enrichment), and UI extensions.
5. **Secure & Trustworthy**: Handle sensitive user data responsibly with encryption, access controls, and auditability.

---

## 3. Current State Assessment
### 3.1 Document Engine & Plugin System
- Parser, processor, and storage plugin abstractions already exist with async processing and background queue support.
- Plugin registry discovers available plugins via configuration.
- Document engine currently optimized for Markdown pipelines but lacks a unified resource domain model.

### 3.2 Notion Integration
- Existing integration manages authentication, database/page retrieval, and basic CRUD operations.
- No linkage yet between documents/resources and Notion entities.

### 3.3 Gaps Identified
- Absence of a canonical `Resource` entity tying content, metadata, storage, and sync state.
- Upload flow lacks persistence, per-user scoping, and progress visibility.
- Notion integration unaware of Core Engine documents or processing status.
- Frontend missing resource library pages and configuration UI for storage/sync plugins.
- No embeddings or RAG hooks to expose resources to AI workflows.

---

## 4. Objectives & Success Criteria
### 4.1 High-Level Objectives
1. Enable users to upload/manage mixed-format resources with rich metadata.
2. Expose resources to AI pipelines (RAG, embeddings) via structured interfaces.
3. Provide optional Notion sync for resource cataloging and visualization without making Notion the source of truth.

### 4.2 User-Facing Success Criteria
- Drag-and-drop uploads with inline progress, error messaging, and retry.
- Searchable resource library with filters (tags, type, project, academic context).
- Ability to configure Notion mapping (database selection, property mapping, visibility) per user or workspace.
- Surfacing of synced Notion links in dashboards and detail views.

### 4.3 Technical Success Criteria
- Storage, parser, and processor plugins remain hot-swappable and are configured via plugin loader.
- Resource metadata indexed for search and future vector retrieval.
- Resilient Notion sync with retries, rate-limit handling, conflict detection, and observability.
- Background processing pipeline instrumented with metrics/logging.

---

## 5. Key Use Cases & User Journeys
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

## 6. Architecture Overview
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

## 7. Data Model & Storage Design
### 7.1 Resource Entity (Core DB)
- `id`, `owner_id`
- `title`, `description`
- `content_uri` (storage location), `content_hash`
- `file_type`, `mime_type`, `size`
- `metadata` JSONB (tags, parser info, academic/project context, external links)
- `processing_status`, `processing_errors`
- `notion_reference` JSONB (page ID, database ID, last sync timestamp, sync status)
- Audit fields (`created_at`, `updated_at`)

### 7.2 Versioning & Relationships
- Version table linking `resource_id` → version number, `content_uri`, `created_at`.
- Many-to-many relationship with tags table or JSON tags for initial iteration.
- Join tables to associate resources with GitHub repos, courses, tasks, or calendar events.

### 7.3 Storage Considerations
- Default persistence in Postgres for metadata + optional file system/S3 for binaries.
- Support external references (Google Docs link) without storing binary by marking `storage_type = external`.
- Streaming uploads and configurable size limits for large files.
- Encryption at rest for stored binaries; hashed filenames to prevent collisions.

---

## 8. API & Service Layer Plan
### 8.1 Backend Endpoints (FastAPI)
- `POST /api/v1/resources/upload` – Multipart upload, returns processing task ID + preliminary metadata.
- `GET /api/v1/resources/:id` – Fetch resource metadata, storage info, Notion status.
- `GET /api/v1/resources` – List/filter resources (pagination, tags, type, search query).
- `GET /api/v1/resources/:id/content` – Stream canonical content if user has permission.
- `POST /api/v1/resources/:id/sync-notion` – Manual sync trigger and configuration override.
- `GET /api/v1/resources/search` – Keyword/semantic search (stub until embeddings ready).

### 8.2 Service Layer Responsibilities
- Document engine orchestrates parser/processor/storage operations via Celery tasks.
- Upload flow: temporary storage → parser selection → metadata extraction → processor hooks → storage commit → Notion sync queue.
- Notion sync worker reads from queue, calls Notion API, updates `notion_reference` fields.
- Storage plugin interfaces extended for metadata-only operations (e.g., linking to external docs).

### 8.3 Access Control & Security
- Per-user scoping enforced at API, DB, and storage layers.
- Role-based permissions for shared resources (future).
- Audit all operations (upload, download, sync) with user ID and timestamps.

---

## 9. Implementation Phases
### Phase 0: Foundations & Prerequisites
- Validate database migrations tooling and create baseline migration for resource tables.
- Finalize configuration schemas (Notion tokens, storage plugin priorities, feature flags).
- Ensure secrets management supports per-user Notion credentials and encryption keys.
- Update developer onboarding docs for new environment variables and plugins.

### Phase 1: Core Resource Ingestion Pipeline
- Create `Resource` SQLAlchemy models and Alembic migrations.
- Implement temporary upload storage (filesystem or object store) with cleanup policies.
- Extend document engine to enqueue parsing/processing tasks upon upload.
- Enhance parser plugins (Markdown, TXT, PDF, DOCX) for metadata extraction; provide stubs for unsupported types.
- Persist parsed content & metadata; expose processing status via API/WebSocket events.

### Phase 2: Storage Plugins & Persistence
- Implement default storage plugin persisting metadata in Postgres and binaries in filesystem/S3.
- Add plugin configuration schema to allow per-user/workspace plugin selection.
- Build admin/CLI tools for listing registered storage plugins and verifying health.
- Provide management API for enabling/disabling storage targets and setting priorities.

### Phase 3: Notion Integration & Sync
- Define Notion database schema recommendations (properties: Title, File Type, Tags, Source, Last Synced, Status).
- Implement Notion sync worker that reads resource updates and pushes to Notion pages.
- Create mapping layer translating resource metadata to Notion properties.
- Handle rate limits and retries with exponential backoff; surface errors in UI & logs.
- Track sync status, timestamps, and Notion page IDs in resource records.

### Phase 4: Frontend Resource Library & Dashboard Surfacing
- Build resource upload modal/component with drag-drop, progress bar, and error states.
- Implement resource listing page with filters, search, tag chips, and sort options.
- Show Notion sync state, provide manual re-sync button, and open Notion page in new tab.
- Integrate resource summaries into dashboard widgets and AI context panels.
- Add settings UI for selecting Notion database, configuring property mapping, and enabling storage plugins.

### Phase 5: AI/RAG Enablement Hooks
- Generate embeddings per resource via pluggable embedding provider (OpenAI, local models, etc.).
- Store embeddings in vector index (e.g., PGVector) tied to resource metadata.
- Expose API endpoints for AI workflows to fetch resources by semantic similarity or metadata filters.
- Provide context packaging (chunking strategy, metadata filters) for downstream AI agents.

### Phase 6: Polishing, Observability & Documentation
- Instrument pipeline with metrics (processing duration, failure rates, Notion sync latency).
- Add user notifications for failed uploads or sync issues (email, in-app alerts).
- Document plugin interfaces, Notion setup guide, troubleshooting steps, and sample configurations.
- Conduct final QA, usability testing, and prepare release notes.

---

## 10. Detailed Workstreams Per Phase
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

## 11. Notion Integration Strategy
### 11.1 Content Mapping
- Core fields → Notion properties (Title, Tags, File Type, Source URL, Last Synced).
- Include Core Engine resource link + optional public share link.
- Store summary/description in Notion for quick scanning.

### 11.2 Database Setup & Configuration
- Recommend dedicated Notion database per workspace (configurable via settings).
- Provide setup wizard guiding users to create/select database, map properties, and authorize integration.
- Allow configuration of Notion template for newly created pages (e.g., default sections for notes, tasks).

### 11.3 Sync Directionality & Conflict Resolution
- MVP: One-way sync (Core Engine → Notion).
- Future: Poll or subscribe to Notion changes (webhooks) to sync status/tags back.
- Conflict policy: Core Engine remains source of truth; Notion edits flagged for manual resolution.

### 11.4 Reliability & Observability
- Queue sync jobs in Celery with exponential backoff on failure.
- Cache Notion metadata to minimize API calls; respect rate limits.
- Provide admin dashboard for sync status, failures, and retry controls.
- Log structured events for monitoring and audit trails.

---

## 12. Security, Privacy & Compliance
- Encrypt stored files at rest; use signed URLs or authenticated streams for downloads.
- Restrict access to resources by user/role; support sharing scopes in future iterations.
- Store Notion access tokens securely (hashed/encrypted) with per-user scoping and revocation flow.
- Provide audit logs for uploads, downloads, Notion sync actions, and configuration changes.
- Consider redaction tools for sensitive data prior to AI enrichment or external sync.
- Ensure GDPR/CCPA compliance for data deletion requests and consent management.

---

## 13. Testing & Validation Plan
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

## 14. Rollout & Migration Strategy
- Gate new resource UI and Notion sync behind feature flags.
- Beta test with internal users to gather feedback on UX, performance, and reliability.
- Provide migration scripts or CLI tools if existing documents need ingestion into new `Resource` model.
- Publish documentation, setup wizard, and video walkthrough for onboarding.
- Establish rollback plan (disable feature flag, revert migrations if necessary).

---

## 15. Risks, Dependencies & Mitigations
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

## 16. Future Extensions & Open Questions
### 16.1 Future Extensions
- Support Google Docs and other cloud sources via connectors (OAuth + API ingestion).
- Build dataset export pipeline for fine-tuning or offline training.
- Introduce marketplace for community storage/processor plugins with discoverability.
- Integrate Notion tasks/calendar bidirectionally for life-management workflows.
- Add automation rules (e.g., auto-tag resources based on Notion properties or GitHub repo metadata).

### 16.2 Open Questions
- Preferred default storage backend (Postgres vs. filesystem)?
- Do we need per-resource sharing controls in MVP or can it wait?
- How to surface AI-generated summaries within Notion without overwriting user content?
- What retention policies should govern large binaries and old versions?
- How should we handle multi-user workspaces with shared Notion databases?

---

## 17. Appendices
### 17.1 Suggested Notion Database Template
| Property | Type | Description |
|----------|------|-------------|
| Name | Title | Resource title |
| Tags | Multi-select | Topics, projects, academic courses |
| File Type | Select | Markdown, PDF, DOCX, TXT, External |
| Source URL | URL | Link back to Core Engine resource detail |
| Last Synced | Date | Timestamp of most recent sync |
| Status | Select | Ingested, Processing, Sync Failed, Archived |
| Summary | Rich text | Short description or AI-generated summary |

### 17.2 Example API Payloads
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

### 17.3 Glossary
- **Resource**: Canonical representation of uploaded or linked knowledge asset.
- **Parser Plugin**: Component that normalizes raw files into structured text + metadata.
- **Processor Plugin**: Component that enriches resources (summaries, tags, embeddings).
- **Storage Plugin**: Component that persists content/metadata or links to external stores.
- **Notion Reference Layer**: Notion database/pages representing resources for user-friendly viewing and organization.
- **RAG**: Retrieval-Augmented Generation; AI technique using external knowledge bases for context.

