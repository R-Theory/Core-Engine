-- Initialize Core Engine Database
-- This script creates the initial database structure

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create initial admin user (for development)
-- Password: admin123 (hashed with bcrypt)
INSERT INTO users (id, email, username, password_hash, first_name, last_name, is_active)
VALUES (
    uuid_generate_v4(),
    'admin@coreengine.dev',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq3F2H.',
    'Admin',
    'User',
    true
) ON CONFLICT (email) DO NOTHING;

-- Insert sample AI agents
INSERT INTO ai_agents (id, name, agent_type, config, is_active) VALUES
(
    uuid_generate_v4(),
    'MetaGPT',
    'code_generation',
    '{"model": "gpt-4", "temperature": 0.7, "max_tokens": 2000}',
    true
),
(
    uuid_generate_v4(),
    'Claude',
    'text_analysis',
    '{"model": "claude-3-sonnet", "temperature": 0.3, "max_tokens": 1500}',
    true
),
(
    uuid_generate_v4(),
    'Perplexity',
    'research',
    '{"model": "perplexity-online", "temperature": 0.5, "max_tokens": 1000}',
    true
) ON CONFLICT (name) DO NOTHING;

-- Insert sample plugins
INSERT INTO plugins (id, name, version, manifest, status) VALUES
(
    uuid_generate_v4(),
    'canvas-integration',
    '1.0.0',
    '{
        "name": "canvas-integration",
        "version": "1.0.0",
        "description": "Canvas LMS integration plugin",
        "author": "Core Engine Team",
        "category": "lms",
        "capabilities": ["sync_courses", "sync_assignments", "read_grades"],
        "config_schema": {
            "canvas_url": {"type": "string", "required": true},
            "api_key": {"type": "string", "required": true, "secret": true}
        },
        "oauth": {
            "provider": "canvas",
            "scopes": ["read:courses", "read:assignments"]
        },
        "permissions": ["network:external", "storage:read", "storage:write"]
    }',
    'active'
),
(
    uuid_generate_v4(),
    'github-integration',
    '1.0.0',
    '{
        "name": "github-integration",
        "version": "1.0.0",
        "description": "GitHub repository integration plugin",
        "author": "Core Engine Team",
        "category": "development",
        "capabilities": ["sync_repos", "analyze_commits", "track_issues"],
        "config_schema": {
            "github_token": {"type": "string", "required": true, "secret": true}
        },
        "oauth": {
            "provider": "github",
            "scopes": ["repo", "read:user"]
        },
        "permissions": ["network:external", "storage:read", "storage:write"]
    }',
    'active'
),
(
    uuid_generate_v4(),
    'google-drive-integration',
    '1.0.0',
    '{
        "name": "google-drive-integration",
        "version": "1.0.0",
        "description": "Google Drive file sync plugin",
        "author": "Core Engine Team",
        "category": "storage",
        "capabilities": ["sync_files", "upload_files", "manage_folders"],
        "config_schema": {
            "folder_id": {"type": "string", "required": false}
        },
        "oauth": {
            "provider": "google",
            "scopes": ["https://www.googleapis.com/auth/drive.readonly"]
        },
        "permissions": ["network:external", "storage:read", "storage:write"]
    }',
    'active'
) ON CONFLICT (name) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_courses_user_id ON courses(user_id);
CREATE INDEX IF NOT EXISTS idx_assignments_course_id ON assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_assignments_due_date ON assignments(due_date);
CREATE INDEX IF NOT EXISTS idx_resources_user_id ON resources(user_id);
CREATE INDEX IF NOT EXISTS idx_resources_type ON resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_resources_tags ON resources USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_interactions_user_id ON agent_interactions(user_id);

-- Enable Row Level Security
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_plugin_configs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (basic user isolation)
CREATE POLICY courses_user_policy ON courses FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
CREATE POLICY assignments_user_policy ON assignments FOR ALL USING (course_id IN (SELECT id FROM courses WHERE user_id = current_setting('app.current_user_id')::uuid));
CREATE POLICY resources_user_policy ON resources FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
CREATE POLICY workflows_user_policy ON workflows FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
CREATE POLICY user_plugin_configs_policy ON user_plugin_configs FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);