//! Professional Template Showcase
//! 
//! This example demonstrates the new professional educational templates
//! available in the Curriculum Curator export system.

use std::path::PathBuf;
use curriculum_curator::content::{ContentType, GeneratedContent};
use curriculum_curator::content::generator::ContentMetadata;
use curriculum_curator::export::{ExportFormat, ExportOptions, HtmlConverter, FormatConverter};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🎓 Professional Educational Template Showcase");
    println!("==============================================\n");

    // Create sample content for demonstration
    let sample_content = create_sample_content();
    
    // List of professional templates to showcase
    let templates = vec![
        ("university", "🏛️  University Course Material"),
        ("corporate", "🏢 Corporate Training"),
        ("k12", "🎒 K-12 Educational Content"),
        ("medical", "🏥 Medical Education"),
        ("stem", "🔬 STEM Education"),
        ("instructor", "👨‍🏫 Instructor's Guide"),
    ];

    let html_converter = HtmlConverter::new();
    
    for (template_name, description) in templates {
        println!("Generating {} template...", description);
        
        let output_path = PathBuf::from(format!("./examples/output/{}_template_example.html", template_name));
        
        // Ensure output directory exists
        if let Some(parent) = output_path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        
        let options = ExportOptions {
            format: ExportFormat::Html,
            output_path: output_path.clone(),
            template_name: Some(template_name.to_string()),
            include_metadata: true,
        };

        let result = html_converter.convert(&[sample_content.clone()], &options).await?;
        
        if result.success {
            println!("✅ {} exported to: {}", description, output_path.display());
            if let Some(size) = result.file_size {
                println!("   File size: {} bytes", size);
            }
        } else {
            println!("❌ Failed to export {}", description);
        }
        println!();
    }

    println!("🎉 All professional templates have been generated!");
    println!("Check the ./examples/output/ directory to see the results.");
    println!("\nTemplate Features:");
    println!("• University: Academic styling with institutional branding");
    println!("• Corporate: Professional business design with metrics dashboard");
    println!("• K-12: Colorful, engaging design for younger learners");
    println!("• Medical: Clinical styling with safety disclaimers");
    println!("• STEM: Tech-focused design with code highlighting");
    println!("• Instructor: Teaching-focused layout with pedagogical aids");

    Ok(())
}

fn create_sample_content() -> GeneratedContent {
    GeneratedContent {
        content_type: ContentType::Slides,
        title: "Introduction to Machine Learning".to_string(),
        content: r#"
---SLIDE---
# Introduction to Machine Learning
## What is Machine Learning?

Machine Learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.

SPEAKER_NOTES:
Start with this foundational definition. Ask students if they can think of examples of ML in their daily lives - smartphones, streaming services, etc.

---SLIDE---
# Types of Machine Learning

## Supervised Learning
- Uses labeled training data
- Examples: Email spam detection, image recognition

## Unsupervised Learning  
- Finds patterns in unlabeled data
- Examples: Customer segmentation, anomaly detection

## Reinforcement Learning
- Learns through trial and error
- Examples: Game playing AI, autonomous vehicles

SPEAKER_NOTES:
Use concrete examples for each type. Consider showing a quick demo or video for reinforcement learning with game-playing AI.

---SLIDE---
# Key Concepts

## Algorithm
The mathematical procedure that finds patterns

## Training Data
The dataset used to teach the algorithm

## Model
The trained algorithm ready to make predictions

## Features
The input variables used to make predictions

SPEAKER_NOTES:
These are the fundamental building blocks. Use analogies - like teaching a child to recognize animals by showing them pictures.

---SLIDE---
# Real-World Applications

- **Healthcare**: Disease diagnosis and drug discovery
- **Finance**: Fraud detection and algorithmic trading  
- **Transportation**: Self-driving cars and route optimization
- **Entertainment**: Content recommendation systems
- **Manufacturing**: Quality control and predictive maintenance

SPEAKER_NOTES:
Encourage students to think about which applications interest them most. This can guide their learning path in ML.

---SLIDE---
# Getting Started with ML

## 1. Learn the Prerequisites
- Statistics and probability
- Linear algebra basics
- Programming (Python recommended)

## 2. Choose Learning Resources
- Online courses (Coursera, edX)
- Books and tutorials
- Hands-on projects

## 3. Practice with Projects
- Start small and build complexity
- Use publicly available datasets
- Join competitions (Kaggle)

SPEAKER_NOTES:
Emphasize that ML is very hands-on. Theory is important, but practical experience is crucial for understanding.
"#.to_string(),
        metadata: ContentMetadata {
            word_count: 285,
            estimated_duration: "45 minutes".to_string(),
            difficulty_level: "Intermediate".to_string(),
        },
    }
}