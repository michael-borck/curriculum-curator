//! Batch Export Example
//! 
//! This example demonstrates the batch export functionality for multiple content types
//! and sessions in the Curriculum Curator. The batch export system allows for:
//! 
//! - Exporting multiple sessions at once
//! - Multiple output formats per job
//! - Parallel processing for performance
//! - Flexible naming strategies
//! - Progress tracking and error handling

use curriculum_curator::export::{
    BatchExportManager, BatchExportJob, BatchExportOptions, ExportFormat, NamingStrategy, BrandingOptions, BrandColors, BrandFonts
};
use curriculum_curator::session::SessionManager;
use curriculum_curator::content::{ContentType, GeneratedContent};
use curriculum_curator::content::generator::ContentMetadata;
use std::path::PathBuf;
use tokio::sync::mpsc;
use uuid::Uuid;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("📦 Batch Export System for Curriculum Curator");
    println!("==============================================\n");

    // Setup demonstration environment
    setup_demo_environment().await?;

    // Create sample sessions and content
    let session_manager = create_session_manager().await?;
    let session_ids = create_sample_sessions(&session_manager).await?;

    println!("✅ Created {} sample sessions with content", session_ids.len());

    // Demonstrate different batch export scenarios
    println!("\n🚀 Demonstrating Batch Export Scenarios:\n");

    // Scenario 1: Multi-format export for single session
    demo_multi_format_export(&session_manager, &session_ids).await?;

    // Scenario 2: Multi-session merged export
    demo_multi_session_export(&session_manager, &session_ids).await?;

    // Scenario 3: Parallel batch processing
    demo_parallel_batch_export(&session_manager, &session_ids).await?;

    // Scenario 4: Custom branding and naming
    demo_branded_batch_export(&session_manager, &session_ids).await?;

    // Scenario 5: Progress tracking
    demo_progress_tracking(&session_manager, &session_ids).await?;

    println!("\n🎉 Batch export demonstration completed!");
    println!("\nGenerated Files:");
    list_generated_files("./examples/batch_output").await?;

    Ok(())
}

async fn setup_demo_environment() -> Result<(), Box<dyn std::error::Error>> {
    // Create output directories
    std::fs::create_dir_all("./examples/batch_output/multi_format")?;
    std::fs::create_dir_all("./examples/batch_output/merged_sessions")?;
    std::fs::create_dir_all("./examples/batch_output/parallel_demo")?;
    std::fs::create_dir_all("./examples/batch_output/branded_export")?;
    std::fs::create_dir_all("./examples/batch_output/progress_demo")?;
    
    Ok(())
}

async fn create_session_manager() -> Result<SessionManager, Box<dyn std::error::Error>> {
    let db_path = "./examples/batch_export_demo.db";
    // Remove existing demo database
    let _ = std::fs::remove_file(db_path);
    
    Ok(SessionManager::new(db_path).await?)
}

async fn create_sample_sessions(session_manager: &SessionManager) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let mut session_ids = Vec::new();

    // Session 1: Introduction to Programming
    let session1 = session_manager.create_session("Introduction to Programming".to_string()).await?;
    let content1 = vec![
        create_content(ContentType::Slides, "Programming Basics", "Variables, functions, and control structures"),
        create_content(ContentType::InstructorNotes, "Teaching Notes", "Key concepts to emphasize"),
        create_content(ContentType::Quiz, "Basic Programming Quiz", "Test student understanding"),
    ];
    for content in content1 {
        session_manager.add_content_to_session(session1.id, &content).await?;
    }
    session_ids.push(session1.id.to_string());

    // Session 2: Data Structures
    let session2 = session_manager.create_session("Data Structures and Algorithms".to_string()).await?;
    let content2 = vec![
        create_content(ContentType::Slides, "Arrays and Lists", "Linear data structures"),
        create_content(ContentType::Worksheet, "Data Structure Exercises", "Hands-on practice"),
        create_content(ContentType::ActivityGuide, "Algorithm Implementation", "Step-by-step guidance"),
    ];
    for content in content2 {
        session_manager.add_content_to_session(session2.id, &content).await?;
    }
    session_ids.push(session2.id.to_string());

    // Session 3: Web Development
    let session3 = session_manager.create_session("Web Development Fundamentals".to_string()).await?;
    let content3 = vec![
        create_content(ContentType::Slides, "HTML and CSS", "Web page structure and styling"),
        create_content(ContentType::InstructorNotes, "Demo Instructions", "Live coding demonstrations"),
        create_content(ContentType::Quiz, "Web Dev Quiz", "HTML/CSS knowledge check"),
        create_content(ContentType::Worksheet, "Build a Website", "Practical exercise"),
    ];
    for content in content3 {
        session_manager.add_content_to_session(session3.id, &content).await?;
    }
    session_ids.push(session3.id.to_string());

    Ok(session_ids)
}

fn create_content(content_type: ContentType, title: &str, description: &str) -> GeneratedContent {
    GeneratedContent {
        content_type,
        title: title.to_string(),
        content: format!("# {}\n\n{}\n\nThis is sample content generated for demonstration purposes.", title, description),
        metadata: ContentMetadata {
            word_count: 50,
            estimated_duration: "15 minutes".to_string(),
            difficulty_level: "Intermediate".to_string(),
        },
    }
}

async fn demo_multi_format_export(
    session_manager: &SessionManager,
    session_ids: &[String],
) -> Result<(), Box<dyn std::error::Error>> {
    println!("📄 Scenario 1: Multi-Format Export for Single Session");
    
    let job = BatchExportJob {
        job_id: "multi_format_demo".to_string(),
        session_ids: vec![session_ids[0].clone()], // First session only
        formats: vec![
            ExportFormat::Html,
            ExportFormat::Pdf,
            ExportFormat::Markdown,
        ],
        output_directory: PathBuf::from("./examples/batch_output/multi_format"),
        naming_strategy: NamingStrategy::ContentBased,
        merge_sessions: false,
        template_name: Some("professional".to_string()),
        include_metadata: true,
        branding_options: None,
    };

    let batch_manager = BatchExportManager::new(session_manager.clone());
    let options = BatchExportOptions::default();

    let result = batch_manager.execute_batch_export(vec![job], options).await?;
    
    println!("   ✅ Exported {} files in {:.2} seconds", 
        result.total_files_created, 
        result.elapsed_time.as_secs_f64()
    );
    println!("   📊 Total size: {} bytes", result.total_size);

    Ok(())
}

async fn demo_multi_session_export(
    session_manager: &SessionManager,
    session_ids: &[String],
) -> Result<(), Box<dyn std::error::Error>> {
    println!("\n📚 Scenario 2: Multi-Session Merged Export");
    
    let job = BatchExportJob {
        job_id: "merged_sessions_demo".to_string(),
        session_ids: session_ids.to_vec(), // All sessions
        formats: vec![ExportFormat::Html, ExportFormat::Pdf],
        output_directory: PathBuf::from("./examples/batch_output/merged_sessions"),
        naming_strategy: NamingStrategy::Custom("complete_curriculum_{timestamp}".to_string()),
        merge_sessions: true, // Combine all session content
        template_name: Some("academic".to_string()),
        include_metadata: true,
        branding_options: None,
    };

    let batch_manager = BatchExportManager::new(session_manager.clone());
    let options = BatchExportOptions::default();

    let result = batch_manager.execute_batch_export(vec![job], options).await?;
    
    println!("   ✅ Merged {} sessions into {} files", 
        session_ids.len(),
        result.total_files_created
    );
    println!("   📊 Processing time: {:.2} seconds", result.elapsed_time.as_secs_f64());

    Ok(())
}

async fn demo_parallel_batch_export(
    session_manager: &SessionManager,
    session_ids: &[String],
) -> Result<(), Box<dyn std::error::Error>> {
    println!("\n⚡ Scenario 3: Parallel Batch Processing");
    
    // Create multiple jobs that will run in parallel
    let jobs = session_ids.iter().enumerate().map(|(i, session_id)| {
        BatchExportJob {
            job_id: format!("parallel_job_{}", i + 1),
            session_ids: vec![session_id.clone()],
            formats: vec![ExportFormat::Html, ExportFormat::Markdown],
            output_directory: PathBuf::from("./examples/batch_output/parallel_demo"),
            naming_strategy: NamingStrategy::SessionBased,
            merge_sessions: false,
            template_name: Some("minimal".to_string()),
            include_metadata: true,
            branding_options: None,
        }
    }).collect();

    let batch_manager = BatchExportManager::new(session_manager.clone());
    let options = BatchExportOptions {
        parallel_exports: true,
        max_concurrent_jobs: 2,
        continue_on_error: true,
        create_manifest: true,
        compress_output: false,
    };

    let start_time = std::time::Instant::now();
    let result = batch_manager.execute_batch_export(jobs, options).await?;
    let parallel_time = start_time.elapsed();
    
    println!("   ✅ Processed {} jobs in parallel", result.total_jobs);
    println!("   ⏱️  Parallel processing time: {:.2} seconds", parallel_time.as_secs_f64());
    println!("   📋 Manifest created: {:?}", result.manifest_path);

    Ok(())
}

async fn demo_branded_batch_export(
    session_manager: &SessionManager,
    session_ids: &[String],
) -> Result<(), Box<dyn std::error::Error>> {
    println!("\n🎨 Scenario 4: Custom Branding and Naming");
    
    let branding = BrandingOptions {
        institution_name: Some("Tech University".to_string()),
        logo_path: None,
        colors: BrandColors {
            primary: "#1E3A8A".to_string(),   // Blue
            secondary: "#64748B".to_string(), // Slate
            accent: "#F59E0B".to_string(),    // Amber
        },
        fonts: BrandFonts {
            heading: "Georgia, serif".to_string(),
            body: "Arial, sans-serif".to_string(),
        },
    };

    let job = BatchExportJob {
        job_id: "branded_export_demo".to_string(),
        session_ids: vec![session_ids[2].clone()], // Web development session
        formats: vec![ExportFormat::Html, ExportFormat::Pdf],
        output_directory: PathBuf::from("./examples/batch_output/branded_export"),
        naming_strategy: NamingStrategy::Custom("TechU_{title}_{format}".to_string()),
        merge_sessions: false,
        template_name: Some("university".to_string()),
        include_metadata: true,
        branding_options: Some(branding),
    };

    let batch_manager = BatchExportManager::new(session_manager.clone());
    let options = BatchExportOptions::default();

    let result = batch_manager.execute_batch_export(vec![job], options).await?;
    
    println!("   ✅ Generated branded exports for Tech University");
    println!("   🎨 Applied custom colors and fonts");
    println!("   📂 Files: {} (Total size: {} bytes)", 
        result.total_files_created, 
        result.total_size
    );

    Ok(())
}

async fn demo_progress_tracking(
    session_manager: &SessionManager,
    session_ids: &[String],
) -> Result<(), Box<dyn std::error::Error>> {
    println!("\n📊 Scenario 5: Progress Tracking");
    
    // Set up progress tracking
    let (progress_tx, mut progress_rx) = mpsc::unbounded_channel();
    
    let job = BatchExportJob {
        job_id: "progress_demo".to_string(),
        session_ids: session_ids.to_vec(),
        formats: vec![ExportFormat::Html],
        output_directory: PathBuf::from("./examples/batch_output/progress_demo"),
        naming_strategy: NamingStrategy::Sequential,
        merge_sessions: false,
        template_name: Some("default".to_string()),
        include_metadata: true,
        branding_options: None,
    };

    let batch_manager = BatchExportManager::new(session_manager.clone())
        .with_progress_tracking(progress_tx);
    let options = BatchExportOptions::default();

    // Start the export in a separate task
    let export_task = tokio::spawn(async move {
        batch_manager.execute_batch_export(vec![job], options).await
    });

    // Monitor progress
    while let Some(progress) = progress_rx.recv().await {
        println!("   📈 Progress: {:.1}% - {} (Job: {:?})", 
            progress.progress_percent,
            progress.current_operation,
            progress.current_job_id
        );
        
        if progress.progress_percent >= 100.0 {
            break;
        }
    }

    let result = export_task.await??;
    println!("   ✅ Progress tracking completed successfully");
    println!("   📊 Final result: {} files, {} errors", 
        result.successful_jobs, 
        result.failed_jobs
    );

    Ok(())
}

async fn list_generated_files(directory: &str) -> Result<(), Box<dyn std::error::Error>> {
    let path = PathBuf::from(directory);
    if path.exists() {
        let mut total_files = 0;
        let mut total_size = 0u64;

        for entry in std::fs::read_dir(&path)? {
            let entry = entry?;
            let metadata = entry.metadata()?;
            
            if metadata.is_file() {
                total_files += 1;
                total_size += metadata.len();
                println!("   📄 {}", entry.path().display());
            } else if metadata.is_dir() {
                // Recursively list subdirectories
                if let Ok(subdir) = std::fs::read_dir(entry.path()) {
                    for sub_entry in subdir {
                        if let Ok(sub_entry) = sub_entry {
                            if sub_entry.metadata()?.is_file() {
                                total_files += 1;
                                total_size += sub_entry.metadata()?.len();
                                println!("   📄 {}", sub_entry.path().display());
                            }
                        }
                    }
                }
            }
        }
        
        println!("\n📈 Summary: {} files, {:.2} KB total", 
            total_files, 
            total_size as f64 / 1024.0
        );
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_batch_export_basic_functionality() {
        let session_manager = create_session_manager().await.unwrap();
        let session_ids = create_sample_sessions(&session_manager).await.unwrap();
        
        let job = BatchExportJob {
            job_id: "test_job".to_string(),
            session_ids: vec![session_ids[0].clone()],
            formats: vec![ExportFormat::Markdown],
            output_directory: PathBuf::from("./test_output"),
            naming_strategy: NamingStrategy::default(),
            merge_sessions: false,
            template_name: None,
            include_metadata: true,
            branding_options: None,
        };

        let batch_manager = BatchExportManager::new(session_manager);
        let options = BatchExportOptions::default();

        let result = batch_manager.execute_batch_export(vec![job], options).await;
        assert!(result.is_ok());
        
        let result = result.unwrap();
        assert_eq!(result.total_jobs, 1);
        assert!(result.successful_jobs > 0);
        
        // Cleanup
        let _ = std::fs::remove_dir_all("./test_output");
    }

    #[test]
    fn test_naming_strategies() {
        // Test different naming strategies work correctly
        let strategies = vec![
            NamingStrategy::SessionBased,
            NamingStrategy::ContentBased,
            NamingStrategy::Sequential,
            NamingStrategy::Custom("test_{job_id}".to_string()),
        ];

        for strategy in strategies {
            // Each strategy should be constructable and serializable
            let _serialized = serde_json::to_string(&strategy).unwrap();
        }
    }
}