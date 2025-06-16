# Batch Export System

The Curriculum Curator's batch export system enables efficient processing of multiple content items across different sessions and formats simultaneously. This system is designed for power users who need to export large amounts of educational content efficiently.

## Overview

The batch export system provides:
- **Multi-session exports**: Export content from multiple sessions at once
- **Multi-format outputs**: Generate multiple file formats in a single operation
- **Parallel processing**: Leverage concurrent execution for improved performance
- **Progress tracking**: Real-time feedback on export operations
- **Flexible naming**: Multiple strategies for output file naming
- **Error resilience**: Continue processing even when some exports fail
- **Manifest generation**: Detailed reports of export operations

## Architecture

### Core Components

```rust
BatchExportManager
├── SessionManager        // Access to content across sessions
├── ExportManager        // Individual format conversion
└── Progress Tracking    // Real-time operation feedback
```

### Data Structures

#### BatchExportJob
```rust
pub struct BatchExportJob {
    pub job_id: String,                           // Unique identifier
    pub session_ids: Vec<String>,                 // Sessions to export
    pub formats: Vec<ExportFormat>,               // Output formats
    pub output_directory: PathBuf,                // Export destination
    pub naming_strategy: NamingStrategy,          // File naming approach
    pub merge_sessions: bool,                     // Combine session content
    pub template_name: Option<String>,            // Template to use
    pub include_metadata: bool,                   // Include generation metadata
    pub branding_options: Option<BrandingOptions>, // Custom branding
}
```

#### BatchExportOptions
```rust
pub struct BatchExportOptions {
    pub parallel_exports: bool,        // Enable concurrent processing
    pub max_concurrent_jobs: usize,    // Limit parallel operations
    pub continue_on_error: bool,       // Don't stop on individual failures
    pub create_manifest: bool,         // Generate operation report
    pub compress_output: bool,         // Compress exported files
}
```

## Usage Examples

### Basic Multi-Format Export

```rust
use curriculum_curator::export::{
    BatchExportManager, BatchExportJob, BatchExportOptions, 
    ExportFormat, NamingStrategy
};

// Create a job to export one session to multiple formats
let job = BatchExportJob {
    job_id: "multi_format_export".to_string(),
    session_ids: vec!["session_123".to_string()],
    formats: vec![
        ExportFormat::Html,
        ExportFormat::Pdf,
        ExportFormat::PowerPoint,
    ],
    output_directory: PathBuf::from("./exports"),
    naming_strategy: NamingStrategy::ContentBased,
    merge_sessions: false,
    template_name: Some("professional".to_string()),
    include_metadata: true,
    branding_options: None,
};

let batch_manager = BatchExportManager::new(session_manager);
let options = BatchExportOptions::default();

let result = batch_manager.execute_batch_export(vec![job], options).await?;
```

### Multi-Session Merged Export

```rust
// Export multiple sessions as a single combined document
let job = BatchExportJob {
    job_id: "complete_course".to_string(),
    session_ids: vec![
        "session_1".to_string(),
        "session_2".to_string(),
        "session_3".to_string(),
    ],
    formats: vec![ExportFormat::Html, ExportFormat::Pdf],
    output_directory: PathBuf::from("./course_materials"),
    naming_strategy: NamingStrategy::Custom("complete_course_{timestamp}".to_string()),
    merge_sessions: true, // Combine all content
    template_name: Some("academic".to_string()),
    include_metadata: true,
    branding_options: Some(university_branding),
};
```

### Parallel Batch Processing

```rust
// Create multiple jobs for parallel execution
let jobs: Vec<BatchExportJob> = session_ids.iter().map(|session_id| {
    BatchExportJob {
        job_id: format!("export_{}", session_id),
        session_ids: vec![session_id.clone()],
        formats: vec![ExportFormat::Html, ExportFormat::Markdown],
        output_directory: PathBuf::from("./individual_exports"),
        naming_strategy: NamingStrategy::SessionBased,
        merge_sessions: false,
        template_name: None,
        include_metadata: true,
        branding_options: None,
    }
}).collect();

let options = BatchExportOptions {
    parallel_exports: true,
    max_concurrent_jobs: 4,  // Process up to 4 jobs simultaneously
    continue_on_error: true,
    create_manifest: true,
    compress_output: false,
};

let result = batch_manager.execute_batch_export(jobs, options).await?;
```

## Naming Strategies

The batch export system supports flexible file naming approaches:

### SessionBased
```rust
NamingStrategy::SessionBased
// Output: session_123.html, session_456.pdf
```

### ContentBased
```rust
NamingStrategy::ContentBased
// Output: Introduction_to_Programming.html, Data_Structures.pdf
```

### Sequential
```rust
NamingStrategy::Sequential
// Output: export_20240315_143022.html, export_20240315_143023.pdf
```

### Custom Patterns
```rust
NamingStrategy::Custom("course_{job_id}_{format}_{timestamp}".to_string())
// Output: course_batch1_html_20240315_143022.html
```

Available placeholders:
- `{job_id}`: The job identifier
- `{timestamp}`: Current timestamp (YYYYMMDD_HHMMSS)
- `{format}`: Export format name (lowercase)
- `{title}`: Content title (sanitized)

## Progress Tracking

Real-time progress monitoring for long-running batch operations:

```rust
use tokio::sync::mpsc;

// Set up progress channel
let (progress_tx, mut progress_rx) = mpsc::unbounded_channel();

let batch_manager = BatchExportManager::new(session_manager)
    .with_progress_tracking(progress_tx);

// Start export in background
let export_task = tokio::spawn(async move {
    batch_manager.execute_batch_export(jobs, options).await
});

// Monitor progress
while let Some(progress) = progress_rx.recv().await {
    println!("Progress: {:.1}% - {}", 
        progress.progress_percent,
        progress.current_operation
    );
    
    if progress.progress_percent >= 100.0 {
        break;
    }
}

let result = export_task.await??;
```

### Progress Information

```rust
pub struct BatchProgress {
    pub total_jobs: usize,              // Total number of jobs
    pub completed_jobs: usize,          // Completed job count
    pub current_job_id: Option<String>, // Currently processing job
    pub current_operation: String,      // Current operation description
    pub progress_percent: f32,          // Overall progress (0-100)
    pub estimated_completion: Option<String>, // ETA if available
    pub errors_encountered: usize,      // Number of errors
}
```

## Error Handling

The batch export system provides robust error handling:

### Continue on Error
```rust
let options = BatchExportOptions {
    continue_on_error: true, // Don't stop the entire batch on single failure
    // ... other options
};
```

### Error Information
```rust
pub struct BatchExportResult {
    pub total_jobs: usize,
    pub successful_jobs: usize,
    pub failed_jobs: usize,
    pub job_results: Vec<JobResult>, // Detailed results per job
    // ... other fields
}

pub struct JobResult {
    pub job_id: String,
    pub success: bool,
    pub export_results: Vec<ExportResult>, // Results per format
    pub error_message: Option<String>,
    // ... other fields
}
```

## Integration with Frontend

### Tauri Commands

#### Create Batch Export Job
```javascript
import { invoke } from '@tauri-apps/api/core';

const job = await invoke('create_batch_export_job', {
  jobId: 'my_export_job',
  sessionIds: ['session_1', 'session_2'],
  formats: ['html', 'pdf'],
  outputDirectory: '/path/to/output',
  namingStrategy: 'content',
  mergeSessions: false,
  templateName: 'professional',
  includeMetadata: true,
  brandingOptions: {
    institutionName: 'My University',
    colors: {
      primary: '#1E3A8A',
      secondary: '#64748B',
      accent: '#F59E0B'
    },
    fonts: {
      heading: 'Georgia, serif',
      body: 'Arial, sans-serif'
    }
  }
});
```

#### Execute Batch Export
```javascript
const result = await invoke('batch_export_content', {
  jobs: [job], // Array of BatchExportJob objects
  options: {
    parallelExports: true,
    maxConcurrentJobs: 4,
    continueOnError: true,
    createManifest: true,
    compressOutput: false
  }
});

console.log(`Exported ${result.totalFilesCreated} files`);
console.log(`Processing time: ${result.elapsedTime} seconds`);
```

### React Hook Example

```typescript
import { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';

interface BatchExportHook {
  exportBatch: (jobs: BatchExportJob[], options?: BatchExportOptions) => Promise<void>;
  isExporting: boolean;
  progress: number;
  result: BatchExportResult | null;
  error: string | null;
}

export function useBatchExport(): BatchExportHook {
  const [isExporting, setIsExporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<BatchExportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const exportBatch = async (jobs: BatchExportJob[], options?: BatchExportOptions) => {
    setIsExporting(true);
    setError(null);
    setProgress(0);

    try {
      const result = await invoke('batch_export_content', { jobs, options });
      setResult(result);
      setProgress(100);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsExporting(false);
    }
  };

  return { exportBatch, isExporting, progress, result, error };
}
```

## Performance Considerations

### Parallel Processing
- **Default Concurrency**: 4 concurrent jobs
- **Memory Usage**: Each job requires memory for content and conversion
- **I/O Bound**: Export operations are primarily disk I/O intensive
- **CPU Usage**: PDF generation and complex HTML rendering are CPU intensive

### Optimization Strategies

1. **Batch Size Management**
   ```rust
   let options = BatchExportOptions {
       max_concurrent_jobs: 2, // Reduce for memory-constrained systems
       // ...
   };
   ```

2. **Content Preloading**
   ```rust
   // Load all session content upfront to reduce database queries
   let content_map = session_manager.get_content_for_sessions(&session_ids).await?;
   ```

3. **Format-Specific Optimization**
   ```rust
   // Group jobs by format for better resource utilization
   let html_jobs = jobs.iter().filter(|j| j.formats.contains(&ExportFormat::Html));
   let pdf_jobs = jobs.iter().filter(|j| j.formats.contains(&ExportFormat::Pdf));
   ```

## Manifest Generation

Batch operations can generate detailed manifests for tracking and auditing:

```json
{
  "batch_export_manifest": {
    "created_at": "2024-03-15T14:30:22Z",
    "total_jobs": 3,
    "successful_jobs": 3,
    "failed_jobs": 0,
    "jobs": [
      {
        "job_id": "multi_format_demo",
        "success": true,
        "files_created": 3,
        "total_size": 156789,
        "exports": [
          {
            "success": true,
            "output_path": "/exports/content.html",
            "file_size": 45123,
            "error_message": null
          },
          {
            "success": true,
            "output_path": "/exports/content.pdf",
            "file_size": 89234,
            "error_message": null
          },
          {
            "success": true,
            "output_path": "/exports/content.md",
            "file_size": 22432,
            "error_message": null
          }
        ]
      }
    ]
  }
}
```

## Advanced Use Cases

### Scheduled Batch Exports
```rust
// Example: Export all sessions daily at 2 AM
use tokio_cron_scheduler::{JobScheduler, Job};

let sched = JobScheduler::new().await?;

sched.add(
    Job::new_async("0 0 2 * * *", |_uuid, _l| {
        Box::pin(async move {
            // Get all sessions
            let sessions = session_manager.list_sessions().await?;
            let session_ids: Vec<String> = sessions.iter()
                .map(|s| s.id.to_string())
                .collect();

            // Create daily backup job
            let job = BatchExportJob {
                job_id: format!("daily_backup_{}", chrono::Utc::now().format("%Y%m%d")),
                session_ids,
                formats: vec![ExportFormat::Html, ExportFormat::Pdf],
                output_directory: PathBuf::from("/backups/daily"),
                naming_strategy: NamingStrategy::SessionBased,
                merge_sessions: false,
                template_name: Some("professional".to_string()),
                include_metadata: true,
                branding_options: None,
            };

            let batch_manager = BatchExportManager::new(session_manager.clone());
            let options = BatchExportOptions::default();

            batch_manager.execute_batch_export(vec![job], options).await?;
            Ok(())
        })
    })?
)?;

sched.start().await?;
```

### Content Filtering and Selection
```rust
// Export only specific content types
impl BatchExportManager {
    pub async fn export_content_by_type(
        &self,
        session_ids: &[String],
        content_types: &[ContentType],
        formats: &[ExportFormat],
        output_dir: &Path,
    ) -> Result<BatchExportResult> {
        // Filter content by type before export
        let filtered_jobs = self.create_filtered_jobs(
            session_ids, 
            content_types, 
            formats, 
            output_dir
        ).await?;

        self.execute_batch_export(filtered_jobs, BatchExportOptions::default()).await
    }
}
```

### Integration with External Systems
```rust
// Example: Export to cloud storage
impl BatchExportManager {
    pub async fn export_to_cloud(
        &self,
        jobs: Vec<BatchExportJob>,
        cloud_config: CloudStorageConfig,
    ) -> Result<BatchExportResult> {
        // Export locally first
        let result = self.execute_batch_export(jobs, BatchExportOptions::default()).await?;

        // Upload successful exports to cloud
        for job_result in &result.job_results {
            if job_result.success {
                for export_result in &job_result.export_results {
                    if export_result.success {
                        cloud_storage.upload(&export_result.output_path, &cloud_config).await?;
                    }
                }
            }
        }

        Ok(result)
    }
}
```

## Best Practices

### Job Organization
1. **Logical Grouping**: Group related sessions in single jobs
2. **Format Selection**: Choose formats based on end-use requirements
3. **Naming Consistency**: Use consistent naming strategies across projects
4. **Output Organization**: Structure output directories logically

### Performance Optimization
1. **Batch Size**: Balance between throughput and resource usage
2. **Parallel Limits**: Set appropriate concurrency based on system resources
3. **Error Handling**: Use continue_on_error for large batches
4. **Progress Monitoring**: Implement progress tracking for long operations

### Error Management
1. **Validation**: Validate job configurations before execution
2. **Retry Logic**: Implement retry for transient failures
3. **Logging**: Comprehensive logging for debugging
4. **Cleanup**: Clean up partial results on failures

### Security Considerations
1. **Path Validation**: Validate output paths to prevent directory traversal
2. **Content Sanitization**: Ensure exported content is safe
3. **Access Control**: Restrict access to batch export functionality
4. **Audit Trails**: Maintain logs of export operations

## Troubleshooting

### Common Issues

**Memory Exhaustion**
```
Error: Out of memory during batch export
```
- Reduce max_concurrent_jobs
- Process smaller batches
- Check available system memory

**File Permission Errors**
```
Error: Permission denied writing to output directory
```
- Verify write permissions on output directory
- Check disk space availability
- Ensure parent directories exist

**Session Not Found**
```
Error: Session not found: session_123
```
- Verify session IDs exist
- Check database connectivity
- Validate session ID format

**Format Conversion Failures**
```
Error: PDF generation failed
```
- Check format-specific dependencies
- Verify template compatibility
- Review content for format-specific issues

### Debug Mode

Enable detailed logging:
```rust
std::env::set_var("BATCH_EXPORT_DEBUG", "1");
std::env::set_var("RUST_LOG", "curriculum_curator::export::batch=debug");
```

This provides detailed information about:
- Job processing order
- Content loading and filtering
- Export operation details
- Error context and stack traces

## Contributing

To contribute to the batch export system:

1. **Test Coverage**: Ensure new features have comprehensive tests
2. **Performance Testing**: Validate performance with realistic workloads
3. **Documentation**: Update documentation for new features
4. **Error Handling**: Provide clear error messages and recovery suggestions
5. **Compatibility**: Maintain backward compatibility with existing APIs