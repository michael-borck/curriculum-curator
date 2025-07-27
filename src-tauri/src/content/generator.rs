use serde::{Deserialize, Serialize};
use anyhow::Result;
use crate::llm::{LLMManager, LLMRequest};
use std::sync::Arc;
use tokio::sync::Mutex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentRequest {
    pub topic: String,
    pub learning_objectives: Vec<String>,
    pub duration: String,
    pub audience: String,
    pub content_types: Vec<ContentType>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum ContentType {
    Slides,
    InstructorNotes,
    Worksheet,
    Quiz,
    ActivityGuide,
}

impl std::fmt::Display for ContentType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ContentType::Slides => write!(f, "slides"),
            ContentType::InstructorNotes => write!(f, "instructor_notes"),
            ContentType::Worksheet => write!(f, "worksheet"),
            ContentType::Quiz => write!(f, "quiz"),
            ContentType::ActivityGuide => write!(f, "activity_guide"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeneratedContent {
    pub content_type: ContentType,
    pub title: String,
    pub content: String,
    pub metadata: ContentMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentMetadata {
    pub word_count: usize,
    pub estimated_duration: String,
    pub difficulty_level: String,
}

pub struct ContentGenerator {
    llm_manager: Arc<Mutex<LLMManager>>,
}

impl ContentGenerator {
    pub fn new(llm_manager: Arc<Mutex<LLMManager>>) -> Self {
        Self { llm_manager }
    }

    pub async fn generate(&self, request: &ContentRequest) -> Result<Vec<GeneratedContent>> {
        let mut generated_content = Vec::new();

        // Generate content for each requested type
        for content_type in &request.content_types {
            let content = self.generate_content_type(request, content_type).await?;
            generated_content.push(content);
        }

        Ok(generated_content)
    }

    async fn generate_content_type(
        &self,
        request: &ContentRequest,
        content_type: &ContentType,
    ) -> Result<GeneratedContent> {
        let prompt = self.build_prompt(request, content_type);
        
        // Create LLM request
        let llm_request = LLMRequest::new(prompt)
            .with_system_prompt("You are an expert educational content creator. Generate high-quality educational materials based on the given specifications.")
            .with_temperature(0.7)
            .with_max_tokens(2000);

        // Generate content using LLM
        let llm_manager = self.llm_manager.lock().await;
        let response = llm_manager.generate(&llm_request).await?;

        // Extract word count from generated content
        let word_count = response.content.split_whitespace().count();
        let difficulty_level = self.estimate_difficulty(request);

        Ok(GeneratedContent {
            content_type: content_type.clone(),
            title: format!("{} - {}", content_type, request.topic),
            content: response.content,
            metadata: ContentMetadata {
                word_count,
                estimated_duration: request.duration.clone(),
                difficulty_level,
            },
        })
    }

    fn build_prompt(&self, request: &ContentRequest, content_type: &ContentType) -> String {
        let base_context = format!(
            "Topic: {}\nAudience: {}\nDuration: {}\n\nLearning Objectives:\n{}",
            request.topic,
            request.audience,
            request.duration,
            request.learning_objectives
                .iter()
                .enumerate()
                .map(|(i, obj)| format!("{}. {}", i + 1, obj))
                .collect::<Vec<_>>()
                .join("\n")
        );

        match content_type {
            ContentType::Slides => format!(
                "{}\n\nCreate a structured slide presentation with:\n\
                - Title slide\n\
                - Learning objectives slide\n\
                - 8-12 content slides with clear headings\n\
                - Activity/discussion slides\n\
                - Summary/conclusion slide\n\n\
                Format as markdown with slide breaks (---). Include speaker notes where helpful.",
                base_context
            ),
            ContentType::InstructorNotes => format!(
                "{}\n\nCreate comprehensive instructor notes including:\n\
                - Lesson preparation checklist\n\
                - Timing guidance for each section\n\
                - Teaching tips and common student misconceptions\n\
                - Discussion prompts and facilitation guidance\n\
                - Assessment strategies\n\
                - Additional resources\n\n\
                Format as detailed markdown documentation.",
                base_context
            ),
            ContentType::Worksheet => format!(
                "{}\n\nCreate a student worksheet with:\n\
                - Clear instructions\n\
                - Varied exercise types (short answer, problem-solving, analysis)\n\
                - Progressive difficulty\n\
                - Space for student responses\n\
                - Extension activities for advanced learners\n\n\
                Format as markdown with clear section breaks.",
                base_context
            ),
            ContentType::Quiz => format!(
                "{}\n\nCreate an assessment quiz with:\n\
                - 10-15 questions of varied types and difficulty\n\
                - Clear instructions\n\
                - Point values for each question\n\
                - Mix of multiple choice, short answer, and essay questions\n\n\
                Format as structured markdown.",
                base_context
            ),
            ContentType::ActivityGuide => format!(
                "{}\n\nCreate an activity guide including:\n\
                - Group exercises\n\
                - Hands-on activities\n\
                - Discussion prompts\n\
                - Problem-solving scenarios\n\
                - Real-world applications\n\n\
                Include timing, materials needed, and facilitation tips.",
                base_context
            ),
        }
    }

    fn estimate_difficulty(&self, request: &ContentRequest) -> String {
        // Simple difficulty estimation based on audience
        if request.audience.to_lowercase().contains("beginner") ||
           request.audience.to_lowercase().contains("elementary") ||
           request.audience.to_lowercase().contains("introductory") {
            "Beginner".to_string()
        } else if request.audience.to_lowercase().contains("advanced") ||
                  request.audience.to_lowercase().contains("expert") ||
                  request.audience.to_lowercase().contains("graduate") {
            "Advanced".to_string()
        } else {
            "Intermediate".to_string()
        }
    }
}