# Template Customization with Branding Options

The Curriculum Curator provides comprehensive branding customization capabilities that allow institutions, organizations, and individual educators to apply their visual identity across all exported educational materials.

## Overview

The branding system enables consistent visual identity across all export formats:
- **HTML exports**: Dynamic CSS with custom colors, fonts, and logos
- **PDF exports**: Branded headers, footers, and typography
- **PowerPoint exports**: Custom themes with institutional colors and fonts
- **Cross-format consistency**: Unified branding across all output types

## Branding Options

### Institution Identity

```rust
BrandingOptions {
    institution_name: Some("State University".to_string()),
    logo_path: Some("/path/to/logo.png".to_string()),
    // ... colors and fonts
}
```

- **Institution Name**: Appears in headers, footers, and title pages
- **Logo**: Integrated into document headers and title slides
- **Custom Metadata**: Branded attribution and generation information

### Color Customization

```rust
BrandColors {
    primary: "#003366".to_string(),     // Main brand color
    secondary: "#0066CC".to_string(),   // Supporting color
    accent: "#FFD700".to_string(),      // Highlight color
}
```

#### Color Usage by Format

| Element | HTML | PDF | PowerPoint |
|---------|------|-----|------------|
| **Primary** | Headers, links | Title elements | Slide themes |
| **Secondary** | Background gradients | Section dividers | Accent elements |
| **Accent** | Buttons, highlights | Callouts | Interactive elements |

### Typography Control

```rust
BrandFonts {
    heading: "Garamond, serif".to_string(),
    body: "Times New Roman, serif".to_string(),
}
```

- **Heading Font**: Used for titles, section headers, and slide headings
- **Body Font**: Used for content text, paragraphs, and body copy
- **Format Compatibility**: Fonts are adapted for web and print compatibility

## Implementation Examples

### University Branding

```rust
let university_branding = BrandingOptions {
    institution_name: Some("State University".to_string()),
    logo_path: Some("data:image/png;base64,iVBORw0...".to_string()),
    colors: BrandColors {
        primary: "#003366".to_string(),   // Navy blue
        secondary: "#0066CC".to_string(), // Royal blue
        accent: "#FFD700".to_string(),    // Gold
    },
    fonts: BrandFonts {
        heading: "Garamond, serif".to_string(),
        body: "Times New Roman, serif".to_string(),
    },
};
```

**Characteristics**:
- Traditional academic colors (navy and gold)
- Serif fonts for academic gravitas
- Formal presentation style
- Institution name prominently displayed

### Corporate Training Branding

```rust
let corporate_branding = BrandingOptions {
    institution_name: Some("TechCorp Training Division".to_string()),
    logo_path: Some("/assets/techcorp-logo.svg".to_string()),
    colors: BrandColors {
        primary: "#1E88E5".to_string(),   // Corporate blue
        secondary: "#424242".to_string(), // Dark gray
        accent: "#FF9800".to_string(),    // Orange
    },
    fonts: BrandFonts {
        heading: "Helvetica Neue, sans-serif".to_string(),
        body: "Arial, sans-serif".to_string(),
    },
};
```

**Characteristics**:
- Modern, professional color scheme
- Sans-serif fonts for contemporary feel
- Clean, minimalist design
- Business-focused presentation

### K-12 School Branding

```rust
let k12_branding = BrandingOptions {
    institution_name: Some("Sunshine Elementary School".to_string()),
    logo_path: Some("/images/school-mascot.png".to_string()),
    colors: BrandColors {
        primary: "#4CAF50".to_string(),   // Green
        secondary: "#2196F3".to_string(), // Blue
        accent: "#FFC107".to_string(),    // Amber
    },
    fonts: BrandFonts {
        heading: "Comic Sans MS, cursive".to_string(),
        body: "Verdana, sans-serif".to_string(),
    },
};
```

**Characteristics**:
- Bright, engaging colors
- Child-friendly fonts
- Playful design elements
- Age-appropriate visual hierarchy

## Usage in Export Operations

### Command Line Interface

```rust
let options = ExportOptions {
    format: ExportFormat::Html,
    output_path: PathBuf::from("branded_content.html"),
    template_name: Some("professional".to_string()),
    include_metadata: true,
    branding_options: Some(branding),
};

let result = export_manager.export_content(&content, &options).await?;
```

### Frontend Integration

```typescript
const exportOptions = {
  format: 'html',
  outputPath: '/exports/branded_lesson.html',
  templateName: 'professional',
  includeMetadata: true,
  brandingOptions: {
    institutionName: 'State University',
    logoPath: 'data:image/png;base64,...',
    colors: {
      primary: '#003366',
      secondary: '#0066CC',
      accent: '#FFD700'
    },
    fonts: {
      heading: 'Garamond, serif',
      body: 'Times New Roman, serif'
    }
  }
};

await invoke('export_content', exportOptions);
```

## Format-Specific Implementation

### HTML Branding

**CSS Custom Properties**:
```css
:root {
  --brand-primary: #003366;
  --brand-secondary: #0066CC;
  --brand-accent: #FFD700;
  --brand-heading-font: Garamond, serif;
  --brand-body-font: Times New Roman, serif;
}
```

**Dynamic Styling**:
- Headers use gradient backgrounds with brand colors
- Typography automatically applies brand fonts
- Logo insertion in document headers
- Responsive design maintains branding across screen sizes

### PDF Branding

**Title Page Customization**:
- Institution name prominently displayed
- Brand colors in headers and dividers
- Custom fonts throughout document
- Logo placement in header/footer areas

**Typography Control**:
- Heading fonts applied to all section titles
- Body fonts used for content text
- Color coordination across all elements

### PowerPoint Branding

**Theme Integration**:
- Custom color schemes in slide master
- Brand fonts in theme definitions
- Logo integration in slide templates
- Consistent visual hierarchy

**XML Customization**:
```xml
<a:clrScheme name="Custom">
  <a:accent1><a:srgbClr val="003366"/></a:accent1>
  <a:accent2><a:srgbClr val="FFD700"/></a:accent2>
</a:clrScheme>
<a:fontScheme name="Custom">
  <a:majorFont><a:latin typeface="Garamond"/></a:majorFont>
  <a:minorFont><a:latin typeface="Times New Roman"/></a:minorFont>
</a:fontScheme>
```

## Logo Integration

### Supported Formats

1. **Data URIs**: Embedded base64-encoded images
   ```
   data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
   ```

2. **File Paths**: References to local or web-accessible images
   ```
   /assets/logos/university-logo.png
   https://university.edu/assets/logo.svg
   ```

3. **Format Optimization**:
   - **HTML**: Direct embedding or CSS background images
   - **PDF**: Image insertion with proper scaling
   - **PowerPoint**: Theme-based logo placement

### Logo Placement

- **HTML**: Header area with responsive sizing
- **PDF**: Title page and optional footer placement
- **PowerPoint**: Slide master integration
- **Consistent Sizing**: Automatic scaling maintains visual balance

## Advanced Customization

### Template-Specific Branding

Different templates can leverage branding in unique ways:

```rust
match template_name {
    "university" => apply_academic_branding(branding),
    "corporate" => apply_business_branding(branding),
    "presentation" => apply_slide_branding(branding),
    _ => apply_default_branding(branding),
}
```

### Conditional Branding

```rust
// Apply branding only if provided
if let Some(branding) = &options.branding_options {
    content = apply_branding_customization(content, branding)?;
}
```

### Inheritance and Defaults

```rust
impl Default for BrandingOptions {
    fn default() -> Self {
        Self {
            institution_name: None,
            logo_path: None,
            colors: BrandColors {
                primary: "#2563eb".to_string(),    // Professional blue
                secondary: "#64748b".to_string(),  // Neutral gray
                accent: "#0ea5e9".to_string(),     // Bright blue
            },
            fonts: BrandFonts {
                heading: "Inter, sans-serif".to_string(),
                body: "Inter, sans-serif".to_string(),
            },
        }
    }
}
```

## Best Practices

### Color Selection

1. **Accessibility**: Ensure sufficient contrast ratios
2. **Print Compatibility**: Consider how colors appear in grayscale
3. **Cultural Considerations**: Be aware of color meanings in different contexts
4. **Brand Guidelines**: Follow institutional color specifications

### Font Selection

1. **Readability**: Choose fonts that are clear at various sizes
2. **Availability**: Use web-safe fonts or provide fallbacks
3. **Consistency**: Maintain hierarchy with heading/body font pairs
4. **Licensing**: Ensure proper licensing for commercial fonts

### Logo Usage

1. **Resolution**: Provide high-resolution images for print formats
2. **Formats**: Use vector formats (SVG) when possible
3. **Sizing**: Ensure logos scale appropriately across formats
4. **Placement**: Follow brand guidelines for logo positioning

### Cross-Format Consistency

1. **Color Accuracy**: Test colors across different output formats
2. **Font Rendering**: Verify fonts display correctly in all formats
3. **Layout Adaptation**: Ensure branding works with different template layouts
4. **Quality Assurance**: Review all exports for brand compliance

## Integration with Settings System

### Frontend Settings Panel

The branding options integrate with the existing settings system:

```typescript
interface ExportSettings {
  defaultFormat: 'pdf' | 'html' | 'markdown' | 'pptx';
  includeMetadata: boolean;
  brandingOptions: BrandingOptions;
  qualitySettings: QualitySettings;
}
```

### Persistent Branding

- Settings are saved across sessions
- Default branding can be applied automatically
- Institution-wide defaults can be configured
- User-specific overrides are supported

## Error Handling

### Validation

```rust
fn validate_branding_options(branding: &BrandingOptions) -> Result<()> {
    // Validate color format (hex codes)
    validate_hex_color(&branding.colors.primary)?;
    validate_hex_color(&branding.colors.secondary)?;
    validate_hex_color(&branding.colors.accent)?;
    
    // Validate font specifications
    validate_font_family(&branding.fonts.heading)?;
    validate_font_family(&branding.fonts.body)?;
    
    // Validate logo path/data URI
    if let Some(logo) = &branding.logo_path {
        validate_logo_format(logo)?;
    }
    
    Ok(())
}
```

### Graceful Degradation

- Invalid colors fall back to defaults
- Missing fonts use system fallbacks
- Logo errors don't break export process
- Partial branding is applied when possible

## Future Enhancements

### Planned Features

1. **Template Marketplace**: Shareable branded templates
2. **Advanced Logo Placement**: Multiple logo positions and sizes
3. **Color Palette Generation**: Automatic complementary color suggestions
4. **Brand Guidelines Compliance**: Automated brand standard checking
5. **Multi-Brand Support**: Different brands for different content types

### Integration Opportunities

1. **Design Systems**: Integration with popular design system formats
2. **Brand Management Tools**: API connections to brand management platforms
3. **Accessibility Tools**: Automated accessibility compliance checking
4. **Print Optimization**: Enhanced print-specific branding features

## Troubleshooting

### Common Issues

**Colors Not Appearing**:
- Verify hex color format (#RRGGBB)
- Check CSS specificity in HTML exports
- Ensure print color settings for PDF exports

**Fonts Not Loading**:
- Confirm font availability on target system
- Provide appropriate font fallbacks
- Test web font loading for HTML exports

**Logo Display Problems**:
- Verify image format compatibility
- Check file path accessibility
- Ensure proper base64 encoding for data URIs

**Cross-Format Inconsistencies**:
- Test exports in all target formats
- Adjust color profiles for print vs. screen
- Validate font rendering across platforms

### Debug Mode

Enable detailed logging for branding operations:

```rust
std::env::set_var("BRANDING_DEBUG", "1");
```

This provides detailed information about:
- Branding option parsing
- Color conversion processes
- Font loading and fallback mechanisms
- Logo processing and embedding

## Contributing

To contribute to the branding system:

1. **Test with Multiple Formats**: Ensure changes work across HTML, PDF, and PowerPoint
2. **Maintain Accessibility**: Preserve accessibility compliance in all customizations
3. **Document Changes**: Update this documentation with new features
4. **Provide Examples**: Include working examples for new branding capabilities
5. **Follow Brand Guidelines**: Respect institutional branding requirements in examples