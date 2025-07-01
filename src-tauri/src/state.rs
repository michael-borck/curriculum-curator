use crate::llm::LLMManager;
use std::sync::Arc;
use tokio::sync::Mutex;

// Application state
pub struct AppState {
    pub llm_manager: Arc<Mutex<LLMManager>>,
}