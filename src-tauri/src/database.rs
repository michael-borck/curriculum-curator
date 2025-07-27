use anyhow::Result;
use uuid::Uuid;
use sqlx::{SqlitePool, Row, migrate::MigrateDatabase};
use serde_json;
use chrono::{DateTime, Utc};
use std::sync::Arc;

use crate::session::Session;
use crate::content::GeneratedContent;

#[derive(Debug, Clone)]
pub struct Database {
    pool: SqlitePool,
}

// Shared database pool type for the entire application
pub type SharedDatabase = Arc<Database>;

impl Database {
    pub async fn new(db_path: &str) -> Result<Self> {
        // Create database if it doesn't exist
        if !sqlx::Sqlite::database_exists(db_path).await.unwrap_or(false) {
            sqlx::Sqlite::create_database(db_path).await?;
        }

        // Connect to database
        let pool = SqlitePool::connect(db_path).await?;
        
        // Run migrations
        sqlx::migrate!("./migrations").run(&pool).await?;
        
        Ok(Self { pool })
    }

    // Create a shared database instance for the entire application
    pub async fn create_shared(db_path: &str) -> Result<SharedDatabase> {
        let db = Self::new(db_path).await?;
        Ok(Arc::new(db))
    }

    // Get access to the underlying pool for direct queries
    pub fn pool(&self) -> &SqlitePool {
        &self.pool
    }

    // Session management
    pub async fn create_session(&mut self, session: &Session) -> Result<()> {
        let content_request_json = serde_json::to_string(&session.content_request)?;
        let config_json = serde_json::to_string(&session.config)?;
        
        sqlx::query(
            "INSERT INTO sessions (id, name, created_at, updated_at, content_request, config) 
             VALUES (?, ?, ?, ?, ?, ?)"
        )
        .bind(session.id.to_string())
        .bind(&session.name)
        .bind(session.created_at.to_rfc3339())
        .bind(session.updated_at.to_rfc3339())
        .bind(content_request_json)
        .bind(config_json)
        .execute(&self.pool).await?;
        
        Ok(())
    }

    pub async fn update_session(&mut self, session: &Session) -> Result<()> {
        let content_request_json = serde_json::to_string(&session.content_request)?;
        let config_json = serde_json::to_string(&session.config)?;
        
        sqlx::query(
            "UPDATE sessions SET name = ?, updated_at = ?, content_request = ?, config = ? WHERE id = ?"
        )
        .bind(&session.name)
        .bind(session.updated_at.to_rfc3339())
        .bind(content_request_json)
        .bind(config_json)
        .bind(session.id.to_string())
        .execute(&self.pool).await?;
        
        Ok(())
    }

    pub async fn get_session(&self, id: Uuid) -> Result<Option<Session>> {
        let row = sqlx::query(
            "SELECT id, name, created_at, updated_at, content_request, config FROM sessions WHERE id = ?"
        )
        .bind(id.to_string())
        .fetch_optional(&self.pool).await?;
        
        if let Some(row) = row {
            let id_str: String = row.get("id");
            let name: String = row.get("name");
            let created_at_str: String = row.get("created_at");
            let updated_at_str: String = row.get("updated_at");
            let content_request_json: Option<String> = row.get("content_request");
            let config_json: String = row.get("config");
            
            let content_request = if let Some(json) = content_request_json {
                serde_json::from_str(&json).ok()
            } else {
                None
            };
            
            let config = serde_json::from_str(&config_json).unwrap_or_default();
            
            Ok(Some(Session {
                id: Uuid::parse_str(&id_str)?,
                name,
                created_at: DateTime::parse_from_rfc3339(&created_at_str)?.with_timezone(&Utc),
                updated_at: DateTime::parse_from_rfc3339(&updated_at_str)?.with_timezone(&Utc),
                content_request,
                generated_content: vec![], // Will be loaded separately
                config,
            }))
        } else {
            Ok(None)
        }
    }

    pub async fn list_sessions(&self) -> Result<Vec<Session>> {
        let rows = sqlx::query(
            "SELECT id, name, created_at, updated_at, content_request, config 
             FROM sessions ORDER BY updated_at DESC"
        ).fetch_all(&self.pool).await?;
        
        let mut sessions = Vec::new();
        for row in rows {
            let id_str: String = row.get("id");
            let name: String = row.get("name");
            let created_at_str: String = row.get("created_at");
            let updated_at_str: String = row.get("updated_at");
            let content_request_json: Option<String> = row.get("content_request");
            let config_json: String = row.get("config");
            
            let content_request = if let Some(json) = content_request_json {
                serde_json::from_str(&json).ok()
            } else {
                None
            };
            
            let config = serde_json::from_str(&config_json).unwrap_or_default();
            
            sessions.push(Session {
                id: Uuid::parse_str(&id_str)?,
                name,
                created_at: DateTime::parse_from_rfc3339(&created_at_str)?.with_timezone(&Utc),
                updated_at: DateTime::parse_from_rfc3339(&updated_at_str)?.with_timezone(&Utc),
                content_request,
                generated_content: vec![], // Will be loaded separately if needed
                config,
            });
        }
        
        Ok(sessions)
    }

    pub async fn delete_session(&mut self, id: Uuid) -> Result<()> {
        sqlx::query("DELETE FROM sessions WHERE id = ?")
            .bind(id.to_string())
            .execute(&self.pool).await?;
        Ok(())
    }

    // Generated content management
    pub async fn save_generated_content(&mut self, session_id: Uuid, content: &GeneratedContent) -> Result<String> {
        let content_id = Uuid::new_v4().to_string();
        let content_json = serde_json::to_string(content)?;
        let metadata_json = serde_json::to_string(&content.metadata)?;
        
        sqlx::query(
            "INSERT INTO generated_content (id, session_id, content_type, title, content, metadata, created_at) 
             VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        .bind(&content_id)
        .bind(session_id.to_string())
        .bind(content.content_type.to_string())
        .bind(&content.title)
        .bind(content_json)
        .bind(metadata_json)
        .bind(Utc::now().to_rfc3339())
        .execute(&self.pool).await?;
        
        Ok(content_id)
    }

    pub async fn get_session_content(&self, session_id: Uuid) -> Result<Vec<GeneratedContent>> {
        let rows = sqlx::query(
            "SELECT content FROM generated_content WHERE session_id = ? ORDER BY created_at"
        )
        .bind(session_id.to_string())
        .fetch_all(&self.pool).await?;
        
        let mut content = Vec::new();
        for row in rows {
            let content_json: String = row.get("content");
            if let Ok(parsed_content) = serde_json::from_str::<GeneratedContent>(&content_json) {
                content.push(parsed_content);
            }
        }
        
        Ok(content)
    }

    // Configuration management
    pub async fn set_config(&mut self, key: &str, value: &str) -> Result<()> {
        sqlx::query(
            "INSERT OR REPLACE INTO app_config (key, value, updated_at) VALUES (?, ?, ?)"
        )
        .bind(key)
        .bind(value)
        .bind(Utc::now().to_rfc3339())
        .execute(&self.pool).await?;
        
        Ok(())
    }

    pub async fn get_config(&self, key: &str) -> Result<Option<String>> {
        let row = sqlx::query(
            "SELECT value FROM app_config WHERE key = ?"
        )
        .bind(key)
        .fetch_optional(&self.pool).await?;
        
        Ok(row.map(|r| r.get::<String, _>("value")))
    }

    // LLM usage tracking
    pub async fn track_llm_usage(
        &self,
        session_id: Uuid,
        provider_id: &str,
        tokens_used: u32,
        cost_usd: Option<f64>,
        request_type: &str,
    ) -> Result<()> {
        sqlx::query(
            "INSERT INTO llm_usage (id, session_id, provider_id, tokens_used, cost_usd, request_type, created_at) 
             VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        .bind(Uuid::new_v4().to_string())
        .bind(session_id.to_string())
        .bind(provider_id)
        .bind(tokens_used as i64)
        .bind(cost_usd)
        .bind(request_type)
        .bind(Utc::now().to_rfc3339())
        .execute(&self.pool).await?;
        
        Ok(())
    }

    pub async fn get_total_cost(&self, session_id: Option<Uuid>) -> Result<f64> {
        let cost_row = if let Some(session_id) = session_id {
            sqlx::query(
                "SELECT COALESCE(SUM(cost_usd), 0.0) as total_cost FROM llm_usage WHERE session_id = ?"
            )
            .bind(session_id.to_string())
            .fetch_one(&self.pool).await?
        } else {
            sqlx::query(
                "SELECT COALESCE(SUM(cost_usd), 0.0) as total_cost FROM llm_usage"
            )
            .fetch_one(&self.pool).await?
        };
        
        Ok(cost_row.get::<f64, _>("total_cost"))
    }
}