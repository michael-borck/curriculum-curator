//! Quarto Integration Example
//! 
//! This example demonstrates the optional Quarto integration for advanced users.
//! Quarto (https://quarto.org) is a scientific and technical publishing system
//! that enables creation of high-quality documents, presentations, and websites.

#[cfg(feature = "quarto-integration")]
use curriculum_curator::export::{ExportFormat, ExportOptions, QuartoConverter, FormatConverter};
use curriculum_curator::content::{ContentType, GeneratedContent};
use curriculum_curator::content::generator::ContentMetadata;
use std::path::PathBuf;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🎓 Quarto Integration for Curriculum Curator");
    println!("============================================\n");

    // Check if Quarto feature is enabled
    #[cfg(not(feature = "quarto-integration"))]
    {
        println!("❌ Quarto integration feature is not enabled.");
        println!("To enable Quarto support, build with:");
        println!("   cargo build --features quarto-integration");
        println!("Or for all features:");
        println!("   cargo build --features full");
        return Ok(());
    }

    #[cfg(feature = "quarto-integration")]
    {
        // Check if Quarto is available on the system
        if !QuartoConverter::is_available() {
            println!("❌ Quarto is not installed or not found in PATH.");
            println!("To use Quarto integration, please install Quarto from:");
            println!("   https://quarto.org/docs/get-started/");
            println!("\nAfter installation, you can:");
            println!("• Generate HTML with interactive features");
            println!("• Create high-quality PDFs via LaTeX");
            println!("• Build professional presentations");
            println!("• Publish to websites and books");
            return Ok(());
        }

        println!("✅ Quarto is available! Setting up integration...\n");

        // Create the Quarto converter
        let quarto_converter = QuartoConverter::new()?;
        let capabilities = quarto_converter.get_capabilities();

        println!("Quarto System Information:");
        println!("• Version: {}", capabilities.version);
        println!("• Python support: {}", if capabilities.has_python { "✅" } else { "❌" });
        println!("• R support: {}", if capabilities.has_r { "✅" } else { "❌" });
        println!("• Julia support: {}", if capabilities.has_julia { "✅" } else { "❌" });
        println!("• Available formats: {:?}", capabilities.available_formats);
        println!();

        // Create sample educational content
        let sample_content = create_sample_educational_content();

        // Test different Quarto export formats
        let formats_to_test = vec![
            (ExportFormat::QuartoHtml, "HTML with Interactive Features", "html"),
            (ExportFormat::QuartoPdf, "High-Quality PDF", "pdf"),
            (ExportFormat::QuartoPowerPoint, "PowerPoint Presentation", "pptx"),
            (ExportFormat::QuartoWord, "Word Document", "docx"),
        ];

        println!("Testing Quarto Export Formats:");
        println!("==============================\n");

        for (format, description, extension) in formats_to_test {
            println!("🚀 Generating {} using Quarto...", description);
            
            let output_path = PathBuf::from(format!("./examples/output/quarto_sample.{}", extension));
            
            // Ensure output directory exists
            if let Some(parent) = output_path.parent() {
                std::fs::create_dir_all(parent)?;
            }
            
            let options = ExportOptions {
                format: format.clone(),
                output_path: output_path.clone(),
                template_name: None,
                include_metadata: true,
            };

            match quarto_converter.convert(&[sample_content.clone()], &options).await {
                Ok(result) => {
                    if result.success {
                        println!("   ✅ Successfully exported to: {}", result.output_path.display());
                        if let Some(size) = result.file_size {
                            println!("   📊 File size: {} bytes", size);
                        }
                    } else {
                        println!("   ❌ Export failed: {}", 
                            result.error_message.unwrap_or_else(|| "Unknown error".to_string()));
                    }
                },
                Err(e) => {
                    println!("   ❌ Export error: {}", e);
                }
            }
            println!();
        }

        println!("🎉 Quarto integration demonstration complete!");
        println!("\nAdvantages of Quarto Integration:");
        println!("• 📄 Single source, multiple outputs (HTML, PDF, PowerPoint, Word)");
        println!("• 🎨 Professional typography and layout");
        println!("• 📊 Interactive elements and code execution");
        println!("• 🔧 Extensive customization options");
        println!("• 📚 Built-in support for academic citations");
        println!("• 🌐 Cross-platform compatibility");
        println!("• 📖 Multi-page books and websites");
        
        println!("\nNext Steps:");
        println!("• Customize templates for your institution");
        println!("• Integrate with your existing workflow");
        println!("• Explore advanced Quarto features");
        println!("• Create reusable template libraries");
    }

    Ok(())
}

fn create_sample_educational_content() -> GeneratedContent {
    GeneratedContent {
        content_type: ContentType::Slides,
        title: "Introduction to Data Science with Quarto".to_string(),
        content: r#"
---SLIDE---
# Introduction to Data Science

## Course Overview

Welcome to our comprehensive introduction to data science! This course will cover:

- Statistical foundations
- Programming with Python/R
- Data visualization techniques
- Machine learning basics
- Real-world applications

SPEAKER_NOTES:
Begin with an icebreaker asking students about their experience with data. Emphasize that this is a beginner-friendly course and prior programming experience is helpful but not required.

---SLIDE---
# What is Data Science?

## Definition

Data science is an interdisciplinary field that combines:

- **Statistics**: Mathematical foundation for analysis
- **Computer Science**: Tools and algorithms
- **Domain Expertise**: Understanding the context

> "Data science is the art of finding insights and patterns in data to solve real-world problems."

SPEAKER_NOTES:
Use the Venn diagram analogy to show how data science sits at the intersection of these three fields. Give examples from different domains (healthcare, business, sports).

---SLIDE---
# The Data Science Workflow

## Key Steps

1. **Problem Definition**: What question are we trying to answer?
2. **Data Collection**: Gathering relevant data sources
3. **Data Cleaning**: Preparing data for analysis
4. **Exploratory Analysis**: Understanding patterns and relationships
5. **Modeling**: Building predictive or descriptive models
6. **Validation**: Testing and refining our approach
7. **Communication**: Presenting findings and insights

SPEAKER_NOTES:
Emphasize that this is not always a linear process. Data scientists often cycle between steps as they learn more about the data and problem domain.

---SLIDE---
# Tools of the Trade

## Programming Languages

- **Python**: Popular, versatile, great libraries (pandas, scikit-learn)
- **R**: Statistical powerhouse, excellent for visualization
- **SQL**: Essential for database queries
- **Julia**: High-performance computing

## Key Libraries & Tools

- **Jupyter Notebooks**: Interactive development environment
- **Git**: Version control for reproducible research
- **Quarto**: Modern publishing system for data science

SPEAKER_NOTES:
We'll be using Quarto in this course for creating reproducible reports that combine code, text, and visualizations. It's the successor to R Markdown and supports multiple languages.

---SLIDE---
# Course Structure

## Module 1: Foundations
- Statistics review
- Programming basics
- Data types and structures

## Module 2: Data Wrangling
- Data cleaning techniques
- Handling missing values
- Data transformation

## Module 3: Visualization
- Principles of effective visualization
- Creating charts and graphs
- Interactive visualizations

## Module 4: Machine Learning
- Supervised learning
- Unsupervised learning
- Model evaluation

SPEAKER_NOTES:
Each module will include hands-on exercises using real datasets. Students will work on a capstone project that applies all concepts learned throughout the course.

---SLIDE---
# Assessment & Projects

## Grading Breakdown

- **Assignments (40%)**: Weekly programming exercises
- **Quizzes (20%)**: Conceptual understanding checks
- **Midterm Project (20%)**: Data analysis report
- **Final Project (20%)**: End-to-end data science project

## Project Guidelines

- Use real-world datasets
- Apply course concepts
- Create reproducible reports using Quarto
- Present findings to the class

SPEAKER_NOTES:
The final project will be presented during the last week of class. Students can choose their own dataset and research question, subject to instructor approval.

---SLIDE---
# Getting Started

## Required Software

1. Install Python or R (or both!)
2. Set up Jupyter/RStudio
3. Install Quarto
4. Create GitHub account
5. Download course materials

## First Assignment

- Complete the development environment setup
- Work through the "Hello Data Science" tutorial
- Submit your first Quarto report

SPEAKER_NOTES:
Technical support will be available during office hours for students who need help with installation. We have a dedicated Slack channel for troubleshooting.

---SLIDE---
# Questions & Next Steps

## Contact Information

- **Instructor**: Dr. Jane Smith
- **Email**: jane.smith@university.edu
- **Office Hours**: Tuesdays 2-4 PM, Room 123
- **Course Website**: www.university.edu/datascience101

## Next Class

We'll dive into statistical foundations and start working with our first dataset!

**Homework**: Read Chapter 1 and complete the environment setup.

SPEAKER_NOTES:
Encourage students to start early on the setup and to reach out if they encounter any issues. Remind them about the course Slack channel for peer support.
"#.to_string(),
        metadata: ContentMetadata {
            word_count: 487,
            estimated_duration: "90 minutes".to_string(),
            difficulty_level: "Beginner".to_string(),
        },
    }
}