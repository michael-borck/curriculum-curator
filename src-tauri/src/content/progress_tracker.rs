use serde::{Deserialize, Serialize};
use anyhow::Result;
use uuid::Uuid;
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use tokio::sync::{broadcast, mpsc};
use crate::content::{ContentType, GenerationContext};

/// Progress tracking and user feedback system for content generation
pub struct ProgressTracker {
    /// Active tracking sessions
    tracking_sessions: HashMap<Uuid, TrackingSession>,
    /// Event broadcaster for real-time updates
    event_broadcaster: broadcast::Sender<ProgressEvent>,
    /// User feedback receiver
    feedback_receiver: mpsc::Receiver<UserFeedbackEvent>,
    /// User feedback sender (for external use)
    feedback_sender: mpsc::Sender<UserFeedbackEvent>,
    /// Progress calculation engine
    progress_calculator: ProgressCalculator,
}

/// Individual tracking session for a generation context
#[derive(Debug, Clone)]
pub struct TrackingSession {
    pub session_id: Uuid,
    pub context_id: Uuid,
    pub started_at: DateTime<Utc>,
    pub estimated_completion: Option<DateTime<Utc>>,
    pub current_phase: GenerationPhase,
    pub overall_progress: ProgressInfo,
    pub phase_progress: HashMap<GenerationPhase, ProgressInfo>,
    pub user_interactions: Vec<UserInteractionRecord>,
    pub milestones: Vec<Milestone>,
    pub metrics: PerformanceMetrics,
    pub status: TrackingStatus,
}

/// Progress events that can be broadcast to listeners
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ProgressEvent {
    /// Generation session started
    SessionStarted {
        session_id: Uuid,
        context_id: Uuid,
        estimated_duration_minutes: u32,
        phases: Vec<GenerationPhase>,
    },
    /// Phase started
    PhaseStarted {
        session_id: Uuid,
        phase: GenerationPhase,
        estimated_duration_minutes: u32,
    },
    /// Progress update within a phase
    ProgressUpdate {
        session_id: Uuid,
        phase: GenerationPhase,
        progress: ProgressInfo,
        message: String,
    },
    /// Milestone reached
    MilestoneReached {
        session_id: Uuid,
        milestone: Milestone,
        overall_progress: f32,
    },
    /// User input required
    UserInputRequired {
        session_id: Uuid,
        interaction_type: InteractionType,
        prompt: String,
        options: Option<Vec<String>>,
        timeout_seconds: Option<u32>,
    },
    /// User feedback received
    UserFeedbackReceived {
        session_id: Uuid,
        feedback_type: FeedbackType,
        response: UserResponse,
    },
    /// Error occurred
    ErrorOccurred {
        session_id: Uuid,
        error: ErrorInfo,
        recovery_options: Vec<RecoveryOption>,
    },
    /// Phase completed
    PhaseCompleted {
        session_id: Uuid,
        phase: GenerationPhase,
        duration_seconds: u64,
        quality_score: Option<f32>,
    },
    /// Session completed
    SessionCompleted {
        session_id: Uuid,
        total_duration_seconds: u64,
        final_quality_score: f32,
        generated_content_types: Vec<ContentType>,
    },
    /// Session paused
    SessionPaused {
        session_id: Uuid,
        reason: PauseReason,
    },
    /// Session resumed
    SessionResumed {
        session_id: Uuid,
        resumed_at: DateTime<Utc>,
    },
    /// Session cancelled
    SessionCancelled {
        session_id: Uuid,
        reason: String,
    },
}

/// User feedback events from the UI
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum UserFeedbackEvent {
    /// Response to a user input request
    InputResponse {
        session_id: Uuid,
        interaction_id: Uuid,
        response: UserResponse,
        response_time_seconds: u64,
    },
    /// Quality rating for generated content
    QualityRating {
        session_id: Uuid,
        content_type: ContentType,
        rating: QualityRating,
        comments: Option<String>,
    },
    /// Request to pause generation
    PauseRequest {
        session_id: Uuid,
        reason: PauseReason,
    },
    /// Request to resume generation
    ResumeRequest {
        session_id: Uuid,
    },
    /// Request to cancel generation
    CancelRequest {
        session_id: Uuid,
        reason: String,
    },
    /// General feedback during generation
    GeneralFeedback {
        session_id: Uuid,
        feedback_type: FeedbackType,
        message: String,
        severity: FeedbackSeverity,
    },
}

/// Phases of content generation
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum GenerationPhase {
    Initialization,         // Setting up generation context
    LearningObjectives,     // Generating learning objectives
    ContentPlanning,        // Planning content structure
    ContentGeneration,      // Generating actual content
    QualityAssurance,       // Quality checks and validation
    UserReview,            // User review and feedback
    Finalization,          // Final processing and packaging
    Export,                // Exporting to final formats
}

/// Progress information for a phase or overall session
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProgressInfo {
    pub percentage: f32,           // 0.0 to 100.0
    pub current_step: String,
    pub total_steps: u32,
    pub completed_steps: u32,
    pub estimated_remaining_minutes: Option<u32>,
    pub current_activity: String,
    pub last_updated: DateTime<Utc>,
}

/// Milestone in the generation process
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Milestone {
    pub milestone_id: Uuid,
    pub name: String,
    pub description: String,
    pub phase: GenerationPhase,
    pub target_percentage: f32,
    pub achieved_at: Option<DateTime<Utc>>,
    pub achievement_data: Option<serde_json::Value>,
}

/// Performance metrics for tracking session
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub total_generation_time_seconds: u64,
    pub phase_durations: HashMap<GenerationPhase, u64>,
    pub api_calls_made: u32,
    pub tokens_processed: u64,
    pub error_count: u32,
    pub user_interaction_count: u32,
    pub average_quality_score: f32,
    pub efficiency_score: f32,    // Based on time vs. estimated time
    pub user_satisfaction_score: Option<f32>,
}

/// Status of a tracking session
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TrackingStatus {
    Active,
    Paused,
    Completed,
    Cancelled,
    Error,
}

/// Types of user interactions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum InteractionType {
    Confirmation,          // Yes/No confirmation
    MultipleChoice,        // Choose from options
    TextInput,            // Free text input
    Rating,               // Rate content quality
    Review,               // Review and approve content
    Customization,        // Customize generation parameters
    ErrorResolution,      // Resolve an error condition
}

/// User response to an interaction
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum UserResponse {
    Confirmation(bool),
    MultipleChoice(String),
    TextInput(String),
    Rating(u32),           // 1-5 or 1-10 scale
    Review {
        approved: bool,
        changes_requested: Vec<String>,
        comments: Option<String>,
    },
    Customization(serde_json::Value),
    ErrorResolution(String),
}

/// Types of user feedback
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FeedbackType {
    Satisfaction,          // General satisfaction
    Quality,              // Content quality feedback
    Performance,          // System performance feedback
    Usability,            // User experience feedback
    Suggestion,           // Feature suggestions
    Bug,                  // Bug reports
    Praise,               // Positive feedback
    Complaint,            // Negative feedback
}

/// Quality rating from user
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QualityRating {
    pub overall_score: u32,        // 1-10 scale
    pub criteria_scores: HashMap<String, u32>, // Specific criteria
    pub would_recommend: Option<bool>,
    pub improvement_suggestions: Vec<String>,
}

/// Severity of feedback
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FeedbackSeverity {
    Info,
    Low,
    Medium,
    High,
    Critical,
}

/// Reasons for pausing generation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PauseReason {
    UserRequest,
    SystemError,
    ResourceLimitation,
    QualityThreshold,
    ExternalDependency,
    ScheduledMaintenance,
}

/// Error information for progress events
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorInfo {
    pub error_id: Uuid,
    pub error_type: String,
    pub message: String,
    pub severity: ErrorSeverity,
    pub phase: GenerationPhase,
    pub recoverable: bool,
    pub occurred_at: DateTime<Utc>,
}

/// Error severity levels
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ErrorSeverity {
    Warning,
    Minor,
    Major,
    Critical,
    Fatal,
}

/// Recovery options for errors
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecoveryOption {
    pub option_id: String,
    pub description: String,
    pub estimated_impact: String,
    pub user_action_required: bool,
}

/// Record of user interaction
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserInteractionRecord {
    pub interaction_id: Uuid,
    pub interaction_type: InteractionType,
    pub prompt: String,
    pub user_response: Option<UserResponse>,
    pub initiated_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
    pub response_time_seconds: Option<u64>,
    pub phase: GenerationPhase,
}

/// Progress calculation engine
#[derive(Debug, Clone)]
pub struct ProgressCalculator {
    /// Weight of each phase in overall progress
    phase_weights: HashMap<GenerationPhase, f32>,
    /// Estimation models for different operations
    estimation_models: HashMap<String, EstimationModel>,
}

/// Model for estimating task duration
#[derive(Debug, Clone)]
pub struct EstimationModel {
    pub base_time_seconds: u64,
    pub complexity_factor: f32,
    pub content_size_factor: f32,
    pub quality_factor: f32,
}

/// Real-time progress notifications
pub struct ProgressNotifier {
    event_sender: broadcast::Sender<ProgressEvent>,
    subscribers: HashMap<Uuid, broadcast::Receiver<ProgressEvent>>,
}

impl ProgressTracker {
    pub fn new() -> Self {
        let (event_broadcaster, _) = broadcast::channel(1000);
        let (feedback_sender, feedback_receiver) = mpsc::channel(100);
        
        Self {
            tracking_sessions: HashMap::new(),
            event_broadcaster,
            feedback_receiver,
            feedback_sender,
            progress_calculator: ProgressCalculator::new(),
        }
    }

    /// Start tracking a new generation session
    pub fn start_tracking(
        &mut self,
        context: &GenerationContext,
    ) -> Result<Uuid> {
        let session_id = Uuid::new_v4();
        let now = Utc::now();
        
        // Calculate estimated completion
        let estimated_duration = self.progress_calculator
            .estimate_total_duration(context);
        let estimated_completion = Some(now + chrono::Duration::seconds(estimated_duration as i64));
        
        // Create tracking session
        let session = TrackingSession {
            session_id,
            context_id: context.context_id,
            started_at: now,
            estimated_completion,
            current_phase: GenerationPhase::Initialization,
            overall_progress: ProgressInfo {
                percentage: 0.0,
                current_step: "Initializing".to_string(),
                total_steps: self.calculate_total_steps(context),
                completed_steps: 0,
                estimated_remaining_minutes: Some((estimated_duration / 60) as u32),
                current_activity: "Setting up generation context".to_string(),
                last_updated: now,
            },
            phase_progress: HashMap::new(),
            user_interactions: Vec::new(),
            milestones: self.create_milestones(context),
            metrics: PerformanceMetrics {
                total_generation_time_seconds: 0,
                phase_durations: HashMap::new(),
                api_calls_made: 0,
                tokens_processed: 0,
                error_count: 0,
                user_interaction_count: 0,
                average_quality_score: 0.0,
                efficiency_score: 1.0,
                user_satisfaction_score: None,
            },
            status: TrackingStatus::Active,
        };

        // Store session
        self.tracking_sessions.insert(session_id, session);

        // Broadcast session started event
        let phases = self.get_planned_phases(context);
        let _ = self.event_broadcaster.send(ProgressEvent::SessionStarted {
            session_id,
            context_id: context.context_id,
            estimated_duration_minutes: (estimated_duration / 60) as u32,
            phases,
        });

        Ok(session_id)
    }

    /// Update progress for a session
    pub fn update_progress(
        &mut self,
        session_id: &Uuid,
        phase: GenerationPhase,
        progress_update: ProgressUpdate,
    ) -> Result<()> {
        if let Some(session) = self.tracking_sessions.get_mut(session_id) {
            // Update phase progress
            let progress_info = ProgressInfo {
                percentage: progress_update.percentage,
                current_step: progress_update.current_step.clone(),
                total_steps: progress_update.total_steps,
                completed_steps: progress_update.completed_steps,
                estimated_remaining_minutes: progress_update.estimated_remaining_minutes,
                current_activity: progress_update.current_activity.clone(),
                last_updated: Utc::now(),
            };

            session.phase_progress.insert(phase.clone(), progress_info.clone());
            session.current_phase = phase.clone();
            
            // Update overall progress
            session.overall_progress = self.progress_calculator
                .calculate_overall_progress(session);

            // Check for milestones (need to handle borrowing)
            let session_id = session.session_id;
            let current_percentage = session.overall_progress.percentage;
            let current_phase = session.current_phase.clone();
            
            // Check milestones without borrowing issues
            let mut milestone_events = Vec::new();
            for milestone in &mut session.milestones {
                if milestone.achieved_at.is_none() && 
                   current_percentage >= milestone.target_percentage &&
                   current_phase == milestone.phase {
                    
                    milestone.achieved_at = Some(Utc::now());
                    milestone_events.push(ProgressEvent::MilestoneReached {
                        session_id,
                        milestone: milestone.clone(),
                        overall_progress: current_percentage,
                    });
                }
            }
            
            // Broadcast milestone events
            for event in milestone_events {
                let _ = self.event_broadcaster.send(event);
            }

            // Broadcast progress update
            let _ = self.event_broadcaster.send(ProgressEvent::ProgressUpdate {
                session_id,
                phase,
                progress: progress_info,
                message: progress_update.message,
            });
        }

        Ok(())
    }

    /// Request user input during generation
    pub fn request_user_input(
        &mut self,
        session_id: &Uuid,
        interaction_type: InteractionType,
        prompt: String,
        options: Option<Vec<String>>,
        timeout_seconds: Option<u32>,
    ) -> Result<Uuid> {
        let interaction_id = Uuid::new_v4();
        
        if let Some(session) = self.tracking_sessions.get_mut(session_id) {
            // Record interaction
            let interaction_record = UserInteractionRecord {
                interaction_id,
                interaction_type: interaction_type.clone(),
                prompt: prompt.clone(),
                user_response: None,
                initiated_at: Utc::now(),
                completed_at: None,
                response_time_seconds: None,
                phase: session.current_phase.clone(),
            };
            
            session.user_interactions.push(interaction_record);
            session.metrics.user_interaction_count += 1;

            // Broadcast user input request
            let _ = self.event_broadcaster.send(ProgressEvent::UserInputRequired {
                session_id: *session_id,
                interaction_type,
                prompt,
                options,
                timeout_seconds,
            });
        }

        Ok(interaction_id)
    }

    /// Handle user feedback
    pub async fn handle_user_feedback(&mut self, feedback: UserFeedbackEvent) -> Result<()> {
        match feedback {
            UserFeedbackEvent::InputResponse { 
                session_id, 
                interaction_id, 
                response, 
                response_time_seconds 
            } => {
                self.process_input_response(session_id, interaction_id, response, response_time_seconds)?;
            }
            UserFeedbackEvent::QualityRating { 
                session_id, 
                content_type, 
                rating,
                comments 
            } => {
                self.process_quality_rating(session_id, content_type, rating, comments)?;
            }
            UserFeedbackEvent::PauseRequest { session_id, reason } => {
                self.pause_session(session_id, reason)?;
            }
            UserFeedbackEvent::ResumeRequest { session_id } => {
                self.resume_session(session_id)?;
            }
            UserFeedbackEvent::CancelRequest { session_id, reason } => {
                self.cancel_session(session_id, reason)?;
            }
            UserFeedbackEvent::GeneralFeedback { 
                session_id, 
                feedback_type, 
                message, 
                severity 
            } => {
                self.process_general_feedback(session_id, feedback_type, message, severity)?;
            }
        }

        Ok(())
    }

    /// Get current progress for a session
    pub fn get_session_progress(&self, session_id: &Uuid) -> Option<&TrackingSession> {
        self.tracking_sessions.get(session_id)
    }

    /// Subscribe to progress events
    pub fn subscribe_to_events(&self) -> broadcast::Receiver<ProgressEvent> {
        self.event_broadcaster.subscribe()
    }

    /// Get feedback sender for external use
    pub fn get_feedback_sender(&self) -> mpsc::Sender<UserFeedbackEvent> {
        self.feedback_sender.clone()
    }

    /// Complete a generation session
    pub fn complete_session(
        &mut self,
        session_id: &Uuid,
        final_quality_score: f32,
        generated_content_types: Vec<ContentType>,
    ) -> Result<()> {
        if let Some(session) = self.tracking_sessions.get_mut(session_id) {
            let now = Utc::now();
            let total_duration = (now - session.started_at).num_seconds() as u64;
            
            session.status = TrackingStatus::Completed;
            session.metrics.total_generation_time_seconds = total_duration;
            session.metrics.average_quality_score = final_quality_score;
            
            // Calculate efficiency score
            let estimated_duration = session.estimated_completion
                .map(|est| (est - session.started_at).num_seconds() as u64)
                .unwrap_or(total_duration);
            
            session.metrics.efficiency_score = if total_duration > 0 {
                estimated_duration as f32 / total_duration as f32
            } else {
                1.0
            };

            // Broadcast completion event
            let _ = self.event_broadcaster.send(ProgressEvent::SessionCompleted {
                session_id: *session_id,
                total_duration_seconds: total_duration,
                final_quality_score,
                generated_content_types,
            });
        }

        Ok(())
    }

    /// Process input response from user
    fn process_input_response(
        &mut self,
        session_id: Uuid,
        interaction_id: Uuid,
        response: UserResponse,
        response_time_seconds: u64,
    ) -> Result<()> {
        if let Some(session) = self.tracking_sessions.get_mut(&session_id) {
            // Find and update the interaction record
            if let Some(interaction) = session.user_interactions.iter_mut()
                .find(|i| i.interaction_id == interaction_id) {
                interaction.user_response = Some(response.clone());
                interaction.completed_at = Some(Utc::now());
                interaction.response_time_seconds = Some(response_time_seconds);
            }

            // Broadcast feedback received event
            let _ = self.event_broadcaster.send(ProgressEvent::UserFeedbackReceived {
                session_id,
                feedback_type: FeedbackType::Quality, // Could be more specific
                response,
            });
        }

        Ok(())
    }

    /// Process quality rating from user
    fn process_quality_rating(
        &mut self,
        session_id: Uuid,
        _content_type: ContentType,
        rating: QualityRating,
        _comments: Option<String>,
    ) -> Result<()> {
        if let Some(session) = self.tracking_sessions.get_mut(&session_id) {
            // Update metrics with quality rating
            let current_avg = session.metrics.average_quality_score;
            let count = session.metrics.user_interaction_count as f32;
            session.metrics.average_quality_score = 
                (current_avg * count + rating.overall_score as f32) / (count + 1.0);
        }

        Ok(())
    }

    /// Pause a generation session
    fn pause_session(&mut self, session_id: Uuid, reason: PauseReason) -> Result<()> {
        if let Some(session) = self.tracking_sessions.get_mut(&session_id) {
            session.status = TrackingStatus::Paused;

            let _ = self.event_broadcaster.send(ProgressEvent::SessionPaused {
                session_id,
                reason,
            });
        }

        Ok(())
    }

    /// Resume a paused session
    fn resume_session(&mut self, session_id: Uuid) -> Result<()> {
        if let Some(session) = self.tracking_sessions.get_mut(&session_id) {
            session.status = TrackingStatus::Active;

            let _ = self.event_broadcaster.send(ProgressEvent::SessionResumed {
                session_id,
                resumed_at: Utc::now(),
            });
        }

        Ok(())
    }

    /// Cancel a generation session
    fn cancel_session(&mut self, session_id: Uuid, reason: String) -> Result<()> {
        if let Some(session) = self.tracking_sessions.get_mut(&session_id) {
            session.status = TrackingStatus::Cancelled;

            let _ = self.event_broadcaster.send(ProgressEvent::SessionCancelled {
                session_id,
                reason,
            });
        }

        Ok(())
    }

    /// Process general feedback
    fn process_general_feedback(
        &mut self,
        _session_id: Uuid,
        _feedback_type: FeedbackType,
        _message: String,
        _severity: FeedbackSeverity,
    ) -> Result<()> {
        // Log feedback for analysis
        // Could be stored in database or analytics system
        Ok(())
    }

    /// Calculate total steps for a context
    fn calculate_total_steps(&self, context: &GenerationContext) -> u32 {
        let base_steps = 10; // Base workflow steps
        let content_steps = context.content_selection.selected_types.len() as u32 * 3;
        let objective_steps = context.learning_objectives.len() as u32;
        
        base_steps + content_steps + objective_steps
    }

    /// Create milestones for a generation context
    fn create_milestones(&self, _context: &GenerationContext) -> Vec<Milestone> {
        vec![
            Milestone {
                milestone_id: Uuid::new_v4(),
                name: "Objectives Complete".to_string(),
                description: "Learning objectives have been generated and approved".to_string(),
                phase: GenerationPhase::LearningObjectives,
                target_percentage: 20.0,
                achieved_at: None,
                achievement_data: None,
            },
            Milestone {
                milestone_id: Uuid::new_v4(),
                name: "Content Outline Ready".to_string(),
                description: "Content structure and outline completed".to_string(),
                phase: GenerationPhase::ContentPlanning,
                target_percentage: 40.0,
                achieved_at: None,
                achievement_data: None,
            },
            Milestone {
                milestone_id: Uuid::new_v4(),
                name: "First Content Generated".to_string(),
                description: "First piece of content has been generated".to_string(),
                phase: GenerationPhase::ContentGeneration,
                target_percentage: 60.0,
                achieved_at: None,
                achievement_data: None,
            },
            Milestone {
                milestone_id: Uuid::new_v4(),
                name: "Quality Check Passed".to_string(),
                description: "All content has passed quality assurance".to_string(),
                phase: GenerationPhase::QualityAssurance,
                target_percentage: 80.0,
                achieved_at: None,
                achievement_data: None,
            },
            Milestone {
                milestone_id: Uuid::new_v4(),
                name: "Generation Complete".to_string(),
                description: "All content has been generated and finalized".to_string(),
                phase: GenerationPhase::Finalization,
                target_percentage: 100.0,
                achieved_at: None,
                achievement_data: None,
            },
        ]
    }

    /// Get planned phases for a context
    fn get_planned_phases(&self, _context: &GenerationContext) -> Vec<GenerationPhase> {
        vec![
            GenerationPhase::Initialization,
            GenerationPhase::LearningObjectives,
            GenerationPhase::ContentPlanning,
            GenerationPhase::ContentGeneration,
            GenerationPhase::QualityAssurance,
            GenerationPhase::UserReview,
            GenerationPhase::Finalization,
            GenerationPhase::Export,
        ]
    }

}

/// Progress update data structure
#[derive(Debug, Clone)]
pub struct ProgressUpdate {
    pub percentage: f32,
    pub current_step: String,
    pub total_steps: u32,
    pub completed_steps: u32,
    pub estimated_remaining_minutes: Option<u32>,
    pub current_activity: String,
    pub message: String,
}

impl ProgressCalculator {
    fn new() -> Self {
        let mut phase_weights = HashMap::new();
        phase_weights.insert(GenerationPhase::Initialization, 0.05);
        phase_weights.insert(GenerationPhase::LearningObjectives, 0.15);
        phase_weights.insert(GenerationPhase::ContentPlanning, 0.15);
        phase_weights.insert(GenerationPhase::ContentGeneration, 0.40);
        phase_weights.insert(GenerationPhase::QualityAssurance, 0.15);
        phase_weights.insert(GenerationPhase::UserReview, 0.05);
        phase_weights.insert(GenerationPhase::Finalization, 0.03);
        phase_weights.insert(GenerationPhase::Export, 0.02);

        Self {
            phase_weights,
            estimation_models: HashMap::new(),
        }
    }

    /// Estimate total duration for a generation context
    fn estimate_total_duration(&self, context: &GenerationContext) -> u64 {
        let base_duration = 600; // 10 minutes base
        let content_factor = context.content_selection.selected_types.len() as u64 * 300; // 5 min per content type
        let complexity_factor = if context.learning_objectives.len() > 5 { 1.5 } else { 1.0 };
        
        ((base_duration + content_factor) as f32 * complexity_factor) as u64
    }

    /// Calculate overall progress from phase progress
    fn calculate_overall_progress(&self, session: &TrackingSession) -> ProgressInfo {
        let mut weighted_progress = 0.0;
        let mut total_weight = 0.0;

        for (phase, weight) in &self.phase_weights {
            if let Some(phase_progress) = session.phase_progress.get(phase) {
                weighted_progress += phase_progress.percentage * weight;
                total_weight += weight;
            }
        }

        let overall_percentage = if total_weight > 0.0 {
            weighted_progress / total_weight
        } else {
            0.0
        };

        ProgressInfo {
            percentage: overall_percentage,
            current_step: session.phase_progress
                .get(&session.current_phase)
                .map(|p| p.current_step.clone())
                .unwrap_or_else(|| "Unknown".to_string()),
            total_steps: session.overall_progress.total_steps,
            completed_steps: (overall_percentage / 100.0 * session.overall_progress.total_steps as f32) as u32,
            estimated_remaining_minutes: self.estimate_remaining_time(session, overall_percentage),
            current_activity: session.phase_progress
                .get(&session.current_phase)
                .map(|p| p.current_activity.clone())
                .unwrap_or_else(|| "Processing".to_string()),
            last_updated: Utc::now(),
        }
    }

    /// Estimate remaining time based on current progress
    fn estimate_remaining_time(&self, session: &TrackingSession, current_percentage: f32) -> Option<u32> {
        if current_percentage <= 0.0 {
            return session.overall_progress.estimated_remaining_minutes;
        }

        let elapsed_seconds = (Utc::now() - session.started_at).num_seconds() as u64;
        let estimated_total_seconds = (elapsed_seconds as f32 / current_percentage * 100.0) as u64;
        let remaining_seconds = estimated_total_seconds.saturating_sub(elapsed_seconds);
        
        Some((remaining_seconds / 60) as u32)
    }
}