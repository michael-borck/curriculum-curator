//! Branding Customization Example
//! 
//! This example demonstrates how to use the template customization system
//! with branding options (colors, logos, fonts) in the Curriculum Curator.

use curriculum_curator::export::{ExportFormat, ExportOptions, ExportManager, BrandingOptions, BrandColors, BrandFonts};
use curriculum_curator::content::{ContentType, GeneratedContent};
use curriculum_curator::content::generator::ContentMetadata;
use std::path::PathBuf;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🎨 Template Customization with Branding Options");
    println!("==============================================\n");

    // Create sample educational content
    let sample_content = create_sample_content();

    // Create different branding configurations
    let university_branding = create_university_branding();
    let corporate_branding = create_corporate_branding();
    let k12_branding = create_k12_branding();

    // Export with different brandings
    let export_manager = ExportManager::new();

    // Test 1: University Branding
    println!("🎓 Testing University Branding...");
    test_branding_export(&export_manager, &sample_content, &university_branding, "university").await?;

    // Test 2: Corporate Branding
    println!("🏢 Testing Corporate Branding...");
    test_branding_export(&export_manager, &sample_content, &corporate_branding, "corporate").await?;

    // Test 3: K-12 School Branding
    println!("🏫 Testing K-12 School Branding...");
    test_branding_export(&export_manager, &sample_content, &k12_branding, "k12").await?;

    // Test 4: No Branding (Default)
    println!("⚪ Testing Default (No Branding)...");
    test_default_export(&export_manager, &sample_content).await?;

    println!("\n🎉 Branding customization demonstration complete!");
    println!("\nBranding Features Demonstrated:");
    println!("• 🎨 Custom color schemes (primary, secondary, accent)");
    println!("• 🔤 Custom fonts (heading and body typography)");
    println!("• 🏛️ Institution name integration");
    println!("• 📄 Cross-format consistency (HTML, PDF, PowerPoint)");
    println!("• 🎯 Template-specific optimizations");
    
    println!("\nGenerated Files:");
    println!("• ./examples/output/university_branded.html");
    println!("• ./examples/output/university_branded.pdf");
    println!("• ./examples/output/university_branded.pptx");
    println!("• ./examples/output/corporate_branded.html");
    println!("• ./examples/output/k12_branded.html");
    println!("• ./examples/output/default_export.html");

    Ok(())
}

async fn test_branding_export(
    manager: &ExportManager,
    content: &GeneratedContent,
    branding: &BrandingOptions,
    prefix: &str
) -> Result<(), Box<dyn std::error::Error>> {
    // Test HTML export with branding
    let html_path = PathBuf::from(format!("./examples/output/{}_branded.html", prefix));
    test_format_with_branding(manager, content, branding, ExportFormat::Html, html_path).await?;

    // Test PDF export with branding
    let pdf_path = PathBuf::from(format!("./examples/output/{}_branded.pdf", prefix));
    test_format_with_branding(manager, content, branding, ExportFormat::Pdf, pdf_path).await?;

    // Test PowerPoint export with branding
    let pptx_path = PathBuf::from(format!("./examples/output/{}_branded.pptx", prefix));
    test_format_with_branding(manager, content, branding, ExportFormat::PowerPoint, pptx_path).await?;

    Ok(())
}

async fn test_format_with_branding(
    manager: &ExportManager,
    content: &GeneratedContent,
    branding: &BrandingOptions,
    format: ExportFormat,
    output_path: PathBuf
) -> Result<(), Box<dyn std::error::Error>> {
    // Ensure output directory exists
    if let Some(parent) = output_path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let options = ExportOptions {
        format: format.clone(),
        output_path: output_path.clone(),
        template_name: Some("professional".to_string()),
        include_metadata: true,
        branding_options: Some(branding.clone()),
    };

    match manager.export_content(&[content.clone()], &options).await {
        Ok(result) => {
            if result.success {
                println!("   ✅ {:?} export successful: {}", format, result.output_path.display());
                if let Some(size) = result.file_size {
                    println!("   📊 File size: {} bytes", size);
                }
            } else {
                println!("   ❌ {:?} export failed: {}", format, 
                    result.error_message.unwrap_or_else(|| "Unknown error".to_string()));
            }
        },
        Err(e) => {
            println!("   ❌ {:?} export error: {}", format, e);
        }
    }

    Ok(())
}

async fn test_default_export(
    manager: &ExportManager,
    content: &GeneratedContent
) -> Result<(), Box<dyn std::error::Error>> {
    let output_path = PathBuf::from("./examples/output/default_export.html");
    
    // Ensure output directory exists
    if let Some(parent) = output_path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let options = ExportOptions {
        format: ExportFormat::Html,
        output_path: output_path.clone(),
        template_name: Some("default".to_string()),
        include_metadata: true,
        branding_options: None, // No branding
    };

    match manager.export_content(&[content.clone()], &options).await {
        Ok(result) => {
            if result.success {
                println!("   ✅ Default export successful: {}", result.output_path.display());
            } else {
                println!("   ❌ Default export failed: {}", 
                    result.error_message.unwrap_or_else(|| "Unknown error".to_string()));
            }
        },
        Err(e) => {
            println!("   ❌ Default export error: {}", e);
        }
    }

    Ok(())
}

fn create_university_branding() -> BrandingOptions {
    BrandingOptions {
        institution_name: Some("State University".to_string()),
        logo_path: None, // Would typically be a path to university logo
        colors: BrandColors {
            primary: "#003366".to_string(),   // Navy blue
            secondary: "#0066CC".to_string(), // Royal blue
            accent: "#FFD700".to_string(),    // Gold
        },
        fonts: BrandFonts {
            heading: "Garamond, serif".to_string(),
            body: "Times New Roman, serif".to_string(),
        },
    }
}

fn create_corporate_branding() -> BrandingOptions {
    BrandingOptions {
        institution_name: Some("TechCorp Training Division".to_string()),
        logo_path: None, // Would typically be a path to company logo
        colors: BrandColors {
            primary: "#1E88E5".to_string(),   // Corporate blue
            secondary: "#424242".to_string(), // Dark gray
            accent: "#FF9800".to_string(),    // Orange
        },
        fonts: BrandFonts {
            heading: "Helvetica Neue, sans-serif".to_string(),
            body: "Arial, sans-serif".to_string(),
        },
    }
}

fn create_k12_branding() -> BrandingOptions {
    BrandingOptions {
        institution_name: Some("Sunshine Elementary School".to_string()),
        logo_path: None, // Would typically be a path to school logo
        colors: BrandColors {
            primary: "#4CAF50".to_string(),   // Green
            secondary: "#2196F3".to_string(), // Blue
            accent: "#FFC107".to_string(),    // Amber
        },
        fonts: BrandFonts {
            heading: "Comic Sans MS, cursive".to_string(),
            body: "Verdana, sans-serif".to_string(),
        },
    }
}

fn create_sample_content() -> GeneratedContent {
    GeneratedContent {
        content_type: ContentType::Slides,
        title: "Introduction to Scientific Method".to_string(),
        content: r#"
---SLIDE---
# The Scientific Method

## Learning Objectives
By the end of this lesson, students will be able to:
- Define the scientific method
- Identify the steps of scientific inquiry
- Apply the scientific method to real-world problems
- Distinguish between observation and inference

---SLIDE---
# What is Science?

## Definition
Science is a systematic way of learning about the natural world through:
- **Observation**: Using our senses to gather information
- **Investigation**: Asking questions and seeking answers
- **Experimentation**: Testing ideas in controlled conditions
- **Analysis**: Making sense of data and evidence

> "Science is not only a disciple of reason but also one of romance and passion." - Stephen Hawking

SPEAKER_NOTES:
Start by asking students what they think science is. Many will think of test tubes and lab coats, but science is much broader. Emphasize that science is a way of thinking and understanding the world around us.

---SLIDE---
# The Scientific Method Steps

## 1. Make an Observation
- Notice something interesting in the natural world
- Ask "What's happening here?"

## 2. Ask a Question
- Form a specific, testable question
- Example: "Why do plants grow toward light?"

## 3. Form a Hypothesis
- Make an educated guess based on prior knowledge
- Must be testable and falsifiable

## 4. Design and Conduct an Experiment
- Control variables
- Collect data systematically

## 5. Analyze Results and Draw Conclusions
- Look for patterns in the data
- Accept, reject, or modify your hypothesis

SPEAKER_NOTES:
Emphasize that this is not always a linear process. Scientists often go back and forth between steps, and new observations can lead to new questions at any point.

---SLIDE---
# Types of Scientific Investigation

## Controlled Experiments
- Test one variable at a time
- Use control groups
- Example: Testing plant growth with different fertilizers

## Observational Studies
- Watch and record natural phenomena
- Cannot control variables
- Example: Studying animal behavior in the wild

## Comparative Studies
- Compare different groups or conditions
- Look for correlations
- Example: Comparing student performance across different teaching methods

SPEAKER_NOTES:
Not all science happens in a laboratory. Field studies, surveys, and observational research are equally important to advancing scientific knowledge.

---SLIDE---
# Designing Good Experiments

## Key Principles

### Variables
- **Independent Variable**: What you change
- **Dependent Variable**: What you measure
- **Control Variables**: What you keep the same

### Controls
- **Positive Control**: Expected to show the effect
- **Negative Control**: Expected to show no effect
- **Control Group**: Receives no treatment

### Sample Size
- Larger samples give more reliable results
- Reduces the impact of individual variation

SPEAKER_NOTES:
Use concrete examples from student experience. For instance, if testing which brand of paper airplane flies farthest, the independent variable is the paper brand, the dependent variable is flight distance, and control variables include throwing force, launch angle, and environmental conditions.

---SLIDE---
# Activity: Design Your Own Experiment

## Question: "Which type of music helps students concentrate better?"

Working in groups, design an experiment to test this question:

1. **Hypothesis**: What do you predict and why?
2. **Variables**: What will you change, measure, and control?
3. **Procedure**: How will you conduct the test?
4. **Data Collection**: What will you record?
5. **Sample Size**: How many people will you test?

**Time**: 15 minutes to plan, 5 minutes to present

SPEAKER_NOTES:
Walk around and guide groups toward good experimental design. Common issues will be controlling variables (same task, same time of day, same volume level) and defining "concentration" (test scores, time to complete task, etc.).

---SLIDE---
# Scientific Thinking in Everyday Life

## Examples of Daily Science

### Weather Prediction
- Observation: Clouds gathering
- Hypothesis: It might rain
- Test: Check weather forecast and barometric pressure

### Cooking
- Observation: Cake didn't rise properly
- Question: What went wrong?
- Hypothesis: Too much/little baking powder
- Test: Try different amounts in next batch

### Problem Solving
- Identify the problem (observation)
- Brainstorm solutions (hypotheses)
- Test the best option (experiment)
- Evaluate results (analysis)

SPEAKER_NOTES:
Help students see that they already use scientific thinking in their daily lives. The formal scientific method just makes this process more systematic and rigorous.

---SLIDE---
# Review and Assessment

## Key Takeaways
1. Science is a way of understanding the natural world
2. The scientific method provides a systematic approach to investigation
3. Good experiments control variables and use appropriate sample sizes
4. Scientific thinking applies to everyday problem-solving

## Next Class
- Applying the scientific method to a real research project
- Introduction to data analysis and interpretation
- Guest speaker: Local scientist discussing their research

**Homework**: Choose a question about the natural world and design an experiment to test it. Use the scientific method steps we learned today.

SPEAKER_NOTES:
Review the main concepts and check for understanding. Assign students to bring their experimental designs to the next class where they'll peer-review each other's work before conducting their investigations.
"#.to_string(),
        metadata: ContentMetadata {
            word_count: 847,
            estimated_duration: "45 minutes".to_string(),
            difficulty_level: "Intermediate".to_string(),
        },
    }
}