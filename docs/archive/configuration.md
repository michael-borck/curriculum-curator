# Configuration Reference

This document details all configuration options available in Curriculum Curator.

## Configuration Files

### Main Configuration (`config.yaml`)

The main configuration file controls application behavior:

```yaml
# Application Settings
app:
  name: "Curriculum Curator"
  version: "1.0.0"
  debug: false
  host: "127.0.0.1"
  port: 5001
  secret_key: ${SECRET_KEY}  # From environment
  
# Database Configuration
database:
  url: ${DATABASE_URL:-sqlite:///data/curriculum.db}
  echo: false
  pool_size: 5
  pool_timeout: 30
  
# Content Storage
storage:
  content_dir: ${CONTENT_DIR:-data/courses}
  upload_dir: ${UPLOAD_DIR:-data/uploads}
  export_dir: ${EXPORT_DIR:-data/exports}
  max_upload_size: 52428800  # 50MB
  allowed_extensions:
    - pdf
    - docx
    - txt
    - md
    - jpg
    - png
    
# Session Configuration
session:
  lifetime: 86400  # 24 hours in seconds
  cookie_name: "curriculum_session"
  secure: true  # HTTPS only in production
  httponly: true
  samesite: "lax"
  
# Authentication
auth:
  password_min_length: 8
  require_email_verification: false
  allow_registration: true
  max_login_attempts: 5
  lockout_duration: 900  # 15 minutes
  
# Teaching Philosophy
teaching_philosophy:
  default_style: "mixed_approach"
  allow_custom_styles: true
  questionnaire_required: true
  styles:
    - traditional_lecture
    - constructivist
    - direct_instruction
    - inquiry_based
    - flipped_classroom
    - project_based
    - competency_based
    - culturally_responsive
    - mixed_approach
    
# Validation Settings
validation:
  enabled: true
  run_on_save: true
  run_on_generate: true
  default_validators:
    - readability
    - structure
    - grammar
  validator_config:
    readability:
      target_grade_level: 12
      min_score: 30
      max_sentence_length: 25
    structure:
      require_headings: true
      max_heading_level: 3
      require_introduction: true
      require_conclusion: true
    grammar:
      check_spelling: true
      check_grammar: true
      language: "en-US"
      
# Remediation Settings
remediation:
  enabled: true
  auto_remediate: false
  require_approval: true
  default_remediators:
    - sentence_splitter
    - format_corrector
  remediator_config:
    sentence_splitter:
      max_length: 20
      preserve_meaning: true
    format_corrector:
      fix_headings: true
      fix_lists: true
      fix_quotes: true
      
# Content Generation
generation:
  default_provider: "openai"
  timeout: 120  # seconds
  max_retries: 3
  streaming: true
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      model: "gpt-4"
      temperature: 0.7
      max_tokens: 4000
    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
      model: "claude-3-opus-20240229"
      temperature: 0.7
      max_tokens: 4000
    local:
      endpoint: "http://localhost:11434"
      model: "llama2"
      
# Export Settings
export:
  formats:
    - markdown
    - html
    - pdf
    - docx
    - latex
  default_format: "markdown"
  include_metadata: true
  include_teaching_notes: false
  templates:
    academic: "templates/academic.html"
    simple: "templates/simple.html"
    
# Feature Flags
features:
  wizard_mode: true
  expert_mode: true
  collaboration: false
  ai_suggestions: true
  advanced_analytics: false
  api_access: true
  
# Logging
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/curriculum.log"
  max_size: 10485760  # 10MB
  backup_count: 5
  
# Performance
performance:
  cache_enabled: true
  cache_ttl: 3600  # 1 hour
  compress_responses: true
  minify_html: true
  
# Security
security:
  csrf_enabled: true
  cors_enabled: false
  cors_origins: []
  rate_limiting:
    enabled: true
    default_limit: "100/minute"
    login_limit: "5/minute"
    generation_limit: "10/hour"
```

## Environment Variables

### Required Variables

```bash
# Security
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///data/curriculum.db

# Storage
CONTENT_DIR=/path/to/content
UPLOAD_DIR=/path/to/uploads
EXPORT_DIR=/path/to/exports
```

### Optional Variables

```bash
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Email (if enabled)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Advanced
WORKERS=4
THREADS=2
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## User Settings

Per-user settings stored in database:

```json
{
  "teaching_philosophy": "constructivist",
  "default_validators": ["readability", "structure"],
  "auto_validate": true,
  "auto_remediate": false,
  "export_format": "pdf",
  "export_template": "academic",
  "ui_preferences": {
    "theme": "light",
    "mode": "expert",
    "show_hints": true
  },
  "llm_preferences": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7
  },
  "notification_preferences": {
    "email_enabled": false,
    "generation_complete": true,
    "weekly_summary": false
  }
}
```

## Course Settings

Per-course configuration:

```json
{
  "teaching_philosophy_override": "project_based",
  "validation_config": {
    "enabled": true,
    "validators": ["readability", "alignment"],
    "custom_rules": []
  },
  "generation_config": {
    "provider": "anthropic",
    "temperature": 0.8,
    "style_emphasis": "practical"
  },
  "export_config": {
    "formats": ["pdf", "html"],
    "include_solutions": false,
    "student_version": true
  },
  "collaboration": {
    "enabled": false,
    "contributors": [],
    "visibility": "private"
  }
}
```

## Plugin Configuration

### Validator Configuration

```yaml
validators:
  readability:
    enabled: true
    config:
      target_reading_level: 12
      max_sentence_words: 25
      min_paragraph_words: 50
      preferred_voice: "active"
      
  structure:
    enabled: true
    config:
      require_title: true
      require_headings: true
      min_sections: 3
      max_heading_depth: 3
      
  grammar:
    enabled: true
    config:
      language: "en-US"
      check_spelling: true
      check_punctuation: true
      style_guide: "academic"
      
  custom_validator:
    enabled: false
    path: "plugins/validators/custom.py"
    config:
      custom_param: "value"
```

### Remediator Configuration

```yaml
remediators:
  sentence_splitter:
    enabled: true
    config:
      max_words: 20
      split_on: ["and", "but", "however"]
      preserve_style: true
      
  format_corrector:
    enabled: true
    config:
      fix_lists: true
      fix_headings: true
      normalize_quotes: true
      
  style_enhancer:
    enabled: false
    config:
      target_style: "academic"
      formality: "high"
```

## LLM Provider Configuration

### OpenAI

```yaml
openai:
  api_key: ${OPENAI_API_KEY}
  organization: ${OPENAI_ORG}  # Optional
  base_url: "https://api.openai.com/v1"  # For proxies
  models:
    default: "gpt-4"
    available:
      - "gpt-4"
      - "gpt-4-turbo-preview"
      - "gpt-3.5-turbo"
  defaults:
    temperature: 0.7
    max_tokens: 4000
    top_p: 1.0
    frequency_penalty: 0.0
    presence_penalty: 0.0
```

### Anthropic

```yaml
anthropic:
  api_key: ${ANTHROPIC_API_KEY}
  base_url: "https://api.anthropic.com"
  models:
    default: "claude-3-opus-20240229"
    available:
      - "claude-3-opus-20240229"
      - "claude-3-sonnet-20240229"
      - "claude-3-haiku-20240307"
  defaults:
    temperature: 0.7
    max_tokens: 4000
```

### Local Models

```yaml
local:
  endpoint: "http://localhost:11434"
  models:
    default: "llama2"
    available:
      - "llama2"
      - "mistral"
      - "codellama"
  defaults:
    temperature: 0.7
    max_tokens: 2048
```

## Export Templates

### Template Configuration

```yaml
templates:
  academic:
    path: "templates/academic.html"
    styles: "templates/academic.css"
    includes:
      - title_page: true
      - table_of_contents: true
      - page_numbers: true
      - headers: true
      
  simple:
    path: "templates/simple.html"
    styles: "templates/simple.css"
    includes:
      - title_page: false
      - table_of_contents: false
      
  presentation:
    path: "templates/presentation.html"
    styles: "templates/presentation.css"
    options:
      - slides_per_page: 1
      - include_notes: true
```

## Advanced Configuration

### Caching

```yaml
cache:
  backend: "redis"  # or "memory"
  redis:
    host: "localhost"
    port: 6379
    db: 0
    password: ${REDIS_PASSWORD}
  ttl:
    default: 3600
    user_data: 300
    generation_results: 86400
```

### Task Queue

```yaml
queue:
  backend: "celery"  # or "rq"
  broker: "redis://localhost:6379/0"
  result_backend: "redis://localhost:6379/1"
  task_time_limit: 300  # 5 minutes
  task_soft_time_limit: 240
```

### Monitoring

```yaml
monitoring:
  metrics:
    enabled: true
    endpoint: "/metrics"
  sentry:
    enabled: false
    dsn: ${SENTRY_DSN}
    environment: ${ENVIRONMENT}
  analytics:
    enabled: false
    google_analytics: ${GA_ID}
```

## Configuration Loading Order

1. Default configuration (built-in)
2. Configuration file (`config.yaml`)
3. Environment variables
4. Database settings (user/course specific)
5. Runtime overrides

## Configuration Validation

On startup, the application validates:

1. Required environment variables
2. File paths exist and are writable
3. API keys are valid format
4. Database connection
5. Plugin configurations

## Best Practices

### Security

1. **Never commit secrets**
   - Use environment variables
   - Use `.env` files (git ignored)
   - Use secret management services

2. **Rotate keys regularly**
   - API keys
   - Secret keys
   - Database passwords

3. **Restrict file access**
   ```bash
   chmod 600 config.yaml
   chmod 600 .env
   ```

### Performance

1. **Cache appropriately**
   - Static content: long TTL
   - User data: short TTL
   - Clear cache on updates

2. **Tune database**
   - Connection pool size
   - Query timeout
   - Index optimization

3. **Monitor resources**
   - Memory usage
   - CPU utilization
   - Disk space

### Maintenance

1. **Version control config**
   - Track changes
   - Document modifications
   - Test before deploying

2. **Backup configuration**
   - Regular backups
   - Test restore process
   - Document dependencies

3. **Update regularly**
   - Security patches
   - Feature updates
   - Dependency updates