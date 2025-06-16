# Quarto Integration for Advanced Users

The Curriculum Curator provides optional integration with [Quarto](https://quarto.org), a scientific and technical publishing system that enables creation of high-quality educational documents, presentations, and websites.

## Overview

Quarto is the next-generation version of R Markdown, built on Pandoc, that supports multiple programming languages and output formats. For educational content creators, Quarto offers:

- **Single Source, Multiple Outputs**: Generate HTML, PDF, PowerPoint, and Word documents from one source
- **Interactive Features**: Code execution, embedded widgets, and dynamic content
- **Professional Typography**: High-quality typesetting with LaTeX integration
- **Academic Features**: Citations, cross-references, and bibliographies
- **Template System**: Customizable templates for institutional branding

## Prerequisites

### System Requirements

1. **Quarto Installation**: Download and install Quarto from [quarto.org](https://quarto.org/docs/get-started/)
2. **Optional Dependencies** (for enhanced features):
   - **Python**: For interactive Python code blocks
   - **R**: For statistical computing and visualization
   - **Julia**: For high-performance computing
   - **LaTeX**: For PDF generation (TeXLive or MiKTeX)

### Feature Flag

Quarto integration is disabled by default to avoid requiring Quarto for basic usage. Enable it when building:

```bash
# Enable Quarto integration only
cargo build --features quarto-integration

# Enable all advanced features
cargo build --features full
```

## Supported Export Formats

The Quarto integration provides these export formats:

| Format | Description | Output | Use Case |
|--------|-------------|---------|----------|
| `QuartoHtml` | Interactive HTML | `.html` | Online learning, interactive content |
| `QuartoPdf` | High-quality PDF | `.pdf` | Print materials, formal documents |
| `QuartoPowerPoint` | Presentation slides | `.pptx` | Classroom presentations |
| `QuartoWord` | Word document | `.docx` | Collaborative editing |
| `QuartoBook` | Multi-chapter book | `.html/.pdf` | Course textbooks, comprehensive guides |
| `QuartoWebsite` | Multi-page website | `.html` | Course websites, online resources |

## Usage Examples

### Basic Export

```rust
use curriculum_curator::export::{ExportFormat, ExportOptions, QuartoConverter, FormatConverter};

// Check if Quarto is available
if QuartoConverter::is_available() {
    let converter = QuartoConverter::new()?;
    
    let options = ExportOptions {
        format: ExportFormat::QuartoHtml,
        output_path: PathBuf::from("output.html"),
        template_name: None,
        include_metadata: true,
    };
    
    let result = converter.convert(&content, &options).await?;
}
```

### Checking Capabilities

```rust
let converter = QuartoConverter::new()?;
let capabilities = converter.get_capabilities();

println!("Quarto version: {}", capabilities.version);
println!("Python support: {}", capabilities.has_python);
println!("R support: {}", capabilities.has_r);
```

## Quarto Document Structure

The converter generates `.qmd` files with this structure:

```yaml
---
title: "Content Title"
date: "2024-01-15"
author: "Curriculum Curator"
format:
  html:
    toc: true
    toc-location: left
    code-tools: true
    theme: cosmo
  pdf:
    documentclass: article
    geometry:
      - margin=1in
execute:
  echo: false
  warning: false
---

# Content Title

::: {.callout-note}
## Content Information
- **Content Type**: Presentation Slides
- **Word Count**: 487 words
- **Estimated Duration**: 90 minutes
- **Difficulty Level**: Beginner
:::

## Slide 1

Content here...

::: {.callout-tip collapse="true"}
## Speaker Notes
Additional notes for instructors...
:::
```

## Content Type Handling

The converter processes different content types optimally for Quarto:

### Slides
- Converts slide separators to Quarto sections
- Transforms speaker notes into collapsible callouts
- Maintains slide hierarchy

### Quizzes
- Creates interactive question blocks
- Uses collapsible callouts for answers
- Formats multiple choice options

### Worksheets
- Converts exercises to structured sections
- Creates answer spaces with proper formatting
- Maintains exercise numbering

### Instructor Notes
- Organizes content into themed callouts
- Uses appropriate icons and styling
- Preserves timing and preparation information

## Template Customization

Quarto supports extensive customization through:

### YAML Configuration
```yaml
format:
  html:
    theme: custom.scss
    css: styles.css
    toc: true
  pdf:
    documentclass: book
    template: custom-template.tex
```

### Custom Templates
- Create institutional templates
- Apply consistent branding
- Customize typography and layout

### CSS Styling
- Override default themes
- Add custom styling
- Ensure accessibility compliance

## Error Handling

The integration includes robust error handling:

```rust
match converter.convert(&content, &options).await {
    Ok(result) => {
        if result.success {
            println!("Export successful: {}", result.output_path.display());
        } else {
            eprintln!("Export failed: {}", result.error_message.unwrap_or_default());
        }
    },
    Err(e) => {
        eprintln!("Conversion error: {}", e);
    }
}
```

## Best Practices

### For Educators
1. **Start Simple**: Begin with basic HTML output, then explore advanced features
2. **Template Libraries**: Create reusable templates for your institution
3. **Version Control**: Use Git to track template and content changes
4. **Batch Processing**: Generate multiple formats simultaneously
5. **Quality Assurance**: Preview outputs before distribution

### For Developers
1. **Feature Detection**: Always check if Quarto is available before use
2. **Graceful Degradation**: Provide fallbacks when Quarto is unavailable
3. **Resource Management**: Clean up temporary files after processing
4. **Error Logging**: Log Quarto execution errors for debugging
5. **Testing**: Test with various content types and formats

## Troubleshooting

### Common Issues

**Quarto Not Found**
```
Error: Quarto executable not found
```
- Ensure Quarto is installed and in PATH
- Try specifying full path to quarto executable

**LaTeX Errors (PDF Generation)**
```
Error: LaTeX compilation failed
```
- Install complete LaTeX distribution (TeXLive/MiKTeX)
- Check for special characters requiring escaping
- Use `--debug` flag to see LaTeX output

**Template Errors**
```
Error: Template not found
```
- Ensure template files are in correct location
- Check template path in configuration
- Validate template syntax

### Debug Mode

Enable verbose logging for troubleshooting:

```rust
// Set environment variable for debug output
std::env::set_var("QUARTO_DEBUG", "1");

let result = converter.convert(&content, &options).await?;
```

## Integration with Export Manager

The Quarto converter integrates seamlessly with the existing export system:

```rust
use curriculum_curator::export::{ExportManager, ExportFormat, ExportOptions};

let manager = ExportManager::new();

// Quarto formats are automatically available if Quarto is installed
let supported_formats = manager.supported_formats();

// Use through the unified interface
let result = manager.export_content(&content, &options).await?;
```

## Performance Considerations

- **Cold Start**: First Quarto execution may be slower due to initialization
- **Resource Usage**: LaTeX PDF generation is memory-intensive
- **Batch Processing**: Process multiple documents in sequence for efficiency
- **Caching**: Quarto caches computations for faster subsequent builds

## Limitations

- **Dependency**: Requires Quarto installation on target system
- **Complexity**: More complex than basic export formats
- **File Size**: Generated documents may be larger due to embedded features
- **Compatibility**: Output quality depends on Quarto version and dependencies

## Future Enhancements

Planned improvements for Quarto integration:

- **Template Marketplace**: Shareable template repository
- **Live Preview**: Real-time preview during editing
- **Custom Extensions**: Support for Quarto extensions
- **Cloud Rendering**: Optional cloud-based rendering service
- **Multi-language**: Enhanced support for international content

## Resources

- [Quarto Documentation](https://quarto.org/docs/)
- [Quarto Gallery](https://quarto.org/docs/gallery/)
- [Template Repository](https://github.com/quarto-dev/quarto-cli/tree/main/src/resources/formats)
- [Community Templates](https://github.com/topics/quarto-template)
- [Academic Writing Guide](https://quarto.org/docs/authoring/scholarly-writing.html)

## Contributing

To contribute to Quarto integration:

1. Test with various Quarto versions
2. Create educational-specific templates
3. Improve error handling and user experience
4. Add support for additional Quarto features
5. Write comprehensive documentation and examples