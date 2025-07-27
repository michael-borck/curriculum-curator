-- SQLite schema for Curriculum Curator
-- Sessions table for managing user sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    content_request TEXT, -- JSON serialized ContentRequest
    config TEXT NOT NULL  -- JSON serialized SessionConfig
);

-- Generated content table for storing all generated content
CREATE TABLE generated_content (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    content_type TEXT NOT NULL, -- Slides, InstructorNotes, Worksheet, Quiz, ActivityGuide
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT NOT NULL, -- JSON serialized ContentMetadata
    created_at DATETIME NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Configuration table for app-wide settings
CREATE TABLE app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- LLM providers configuration
CREATE TABLE llm_providers (
    id TEXT PRIMARY KEY,
    provider_type TEXT NOT NULL, -- Ollama, OpenAI, Claude, Gemini
    name TEXT NOT NULL,
    api_key_stored BOOLEAN NOT NULL DEFAULT 0, -- Whether API key is stored in keyring
    config TEXT NOT NULL, -- JSON serialized provider-specific config
    is_enabled BOOLEAN NOT NULL DEFAULT 1,
    is_default BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Cost tracking for LLM usage
CREATE TABLE llm_usage (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    tokens_used INTEGER NOT NULL,
    cost_usd REAL,
    request_type TEXT NOT NULL, -- content_generation, validation, etc.
    created_at DATETIME NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES llm_providers(id)
);

-- Templates for content generation
CREATE TABLE content_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    content_type TEXT NOT NULL,
    template_content TEXT NOT NULL,
    variables TEXT NOT NULL, -- JSON array of variable names
    is_system BOOLEAN NOT NULL DEFAULT 0, -- System vs user-created templates
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Validation results history
CREATE TABLE validation_results (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL,
    validator_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    score REAL NOT NULL,
    issues TEXT NOT NULL, -- JSON serialized ValidationIssue array
    suggestions TEXT NOT NULL, -- JSON array of suggestions
    created_at DATETIME NOT NULL,
    FOREIGN KEY (content_id) REFERENCES generated_content(id) ON DELETE CASCADE
);

-- Export history
CREATE TABLE export_history (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    export_format TEXT NOT NULL,
    output_path TEXT NOT NULL,
    file_size INTEGER,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes for better performance
CREATE INDEX idx_sessions_created_at ON sessions(created_at);
CREATE INDEX idx_sessions_updated_at ON sessions(updated_at);
CREATE INDEX idx_generated_content_session_id ON generated_content(session_id);
CREATE INDEX idx_generated_content_created_at ON generated_content(created_at);
CREATE INDEX idx_llm_usage_session_id ON llm_usage(session_id);
CREATE INDEX idx_llm_usage_created_at ON llm_usage(created_at);
CREATE INDEX idx_validation_results_content_id ON validation_results(content_id);
CREATE INDEX idx_export_history_session_id ON export_history(session_id);