# Phase 1: Fix Core Import/Export - Technical Specifications

## Overview
Phase 1 establishes the foundation for true curriculum curation by fixing import functionality and enhancing export capabilities. This phase transforms the app from a pure content generator to a content curator.

**Duration**: 2-3 weeks  
**Goal**: Enable true curation by fixing import functionality and enhancing export

## 1.1 Fix Import Infrastructure

### 1.1.1 Add XML Parsing Library

**Current Issue**: Import functionality is disabled due to missing XML parsing dependencies.

**Root Cause Analysis**:
```rust
// File: src-tauri/src/import/parsers.rs (currently disabled)
// Error: "quick-xml API compatibility issues"
// Real Issue: No XML parsing library in Cargo.toml
```

**Solution**:
```toml
# Add to src-tauri/Cargo.toml
[dependencies]
quick-xml = "0.31"
zip = "0.6"        # For .pptx/.docx extraction
```

**Implementation Steps**:
1. Add dependencies to `Cargo.toml`
2. Re-enable parsers in `src-tauri/src/import/parsers.rs`
3. Update imports and error handling
4. Test with sample files

### 1.1.2 PowerPoint (.pptx) Parser

**File Structure**:
```
presentation.pptx
├── [Content_Types].xml
├── _rels/
│   └── .rels
├── ppt/
│   ├── presentation.xml
│   ├── slides/
│   │   ├── slide1.xml
│   │   ├── slide2.xml
│   │   └── ...
│   ├── slideLayouts/
│   ├── slideMasters/
│   └── notesSlides/
└── docProps/
    ├── core.xml
    └── app.xml
```

**Technical Implementation**:

```rust
// File: src-tauri/src/import/powerpoint.rs
use quick_xml::Reader;
use zip::ZipArchive;
use std::io::BufReader;

#[derive(Debug, Clone)]
pub struct PowerPointSlide {
    pub slide_number: u32,
    pub title: Option<String>,
    pub content: Vec<String>,
    pub speaker_notes: Option<String>,
    pub images: Vec<String>,
    pub animations: Vec<Animation>,
}

#[derive(Debug, Clone)]
pub struct PowerPointPresentation {
    pub title: String,
    pub slides: Vec<PowerPointSlide>,
    pub total_slides: u32,
    pub metadata: PresentationMetadata,
}

pub struct PowerPointParser;

impl PowerPointParser {
    pub fn parse(file_path: &Path) -> Result<PowerPointPresentation, ImportError> {
        let file = File::open(file_path)?;
        let mut archive = ZipArchive::new(file)?;
        
        // 1. Extract presentation.xml for metadata
        let metadata = Self::extract_metadata(&mut archive)?;
        
        // 2. Extract slide relationships
        let slide_files = Self::get_slide_files(&mut archive)?;
        
        // 3. Parse each slide
        let mut slides = Vec::new();
        for (index, slide_file) in slide_files.iter().enumerate() {
            let slide = Self::parse_slide(&mut archive, slide_file, index as u32 + 1)?;
            slides.push(slide);
        }
        
        // 4. Extract speaker notes
        Self::extract_speaker_notes(&mut archive, &mut slides)?;
        
        Ok(PowerPointPresentation {
            title: metadata.title,
            slides,
            total_slides: slides.len() as u32,
            metadata,
        })
    }
    
    fn extract_metadata(archive: &mut ZipArchive<File>) -> Result<PresentationMetadata, ImportError> {
        let core_xml = Self::read_zip_file(archive, "docProps/core.xml")?;
        let app_xml = Self::read_zip_file(archive, "docProps/app.xml")?;
        
        // Parse XML to extract title, author, etc.
        // Implementation details...
    }
    
    fn parse_slide(
        archive: &mut ZipArchive<File>, 
        slide_path: &str, 
        slide_number: u32
    ) -> Result<PowerPointSlide, ImportError> {
        let slide_xml = Self::read_zip_file(archive, slide_path)?;
        let mut reader = Reader::from_str(&slide_xml);
        
        let mut title = None;
        let mut content = Vec::new();
        let mut images = Vec::new();
        
        loop {
            match reader.read_event() {
                Ok(Event::Start(ref e)) => {
                    match e.name().as_ref() {
                        b"a:t" => {
                            // Extract text content
                            let text = Self::extract_text(&mut reader)?;
                            if title.is_none() && Self::is_title_placeholder(&text) {
                                title = Some(text);
                            } else {
                                content.push(text);
                            }
                        },
                        b"a:blip" => {
                            // Extract image references
                            if let Some(embed_id) = Self::get_attribute(e, "r:embed") {
                                images.push(embed_id);
                            }
                        },
                        _ => {}
                    }
                },
                Ok(Event::Eof) => break,
                Err(e) => return Err(ImportError::XmlParse(e.to_string())),
                _ => {}
            }
        }
        
        Ok(PowerPointSlide {
            slide_number,
            title,
            content,
            speaker_notes: None, // Will be filled later
            images,
            animations: Vec::new(), // TODO: Parse animations
        })
    }
}
```

### 1.1.3 Word (.docx) Parser

**File Structure**:
```
document.docx
├── [Content_Types].xml
├── _rels/
│   └── .rels
├── word/
│   ├── document.xml
│   ├── styles.xml
│   ├── numbering.xml
│   └── _rels/
│       └── document.xml.rels
└── docProps/
    ├── core.xml
    └── app.xml
```

**Technical Implementation**:

```rust
// File: src-tauri/src/import/word.rs
#[derive(Debug, Clone)]
pub struct WordDocument {
    pub title: String,
    pub sections: Vec<DocumentSection>,
    pub styles: Vec<Style>,
    pub metadata: DocumentMetadata,
}

#[derive(Debug, Clone)]
pub struct DocumentSection {
    pub heading: Option<String>,
    pub level: u32,
    pub content: String,
    pub content_type: DetectedContentType,
    pub formatting: SectionFormatting,
}

#[derive(Debug, Clone)]
pub enum DetectedContentType {
    LearningObjectives,
    ContentOutline,
    Assessment,
    Instructions,
    GeneralContent,
}

pub struct WordParser;

impl WordParser {
    pub fn parse(file_path: &Path) -> Result<WordDocument, ImportError> {
        let file = File::open(file_path)?;
        let mut archive = ZipArchive::new(file)?;
        
        // 1. Extract document.xml
        let document_xml = Self::read_zip_file(&mut archive, "word/document.xml")?;
        
        // 2. Parse styles for structure detection
        let styles = Self::parse_styles(&mut archive)?;
        
        // 3. Parse document structure
        let sections = Self::parse_document_structure(&document_xml, &styles)?;
        
        // 4. Extract metadata
        let metadata = Self::extract_metadata(&mut archive)?;
        
        Ok(WordDocument {
            title: metadata.title.clone(),
            sections,
            styles,
            metadata,
        })
    }
    
    fn parse_document_structure(
        document_xml: &str, 
        styles: &[Style]
    ) -> Result<Vec<DocumentSection>, ImportError> {
        let mut reader = Reader::from_str(document_xml);
        let mut sections = Vec::new();
        let mut current_section = None;
        let mut current_paragraph = String::new();
        
        loop {
            match reader.read_event() {
                Ok(Event::Start(ref e)) => {
                    match e.name().as_ref() {
                        b"w:p" => {
                            // Start of paragraph
                            current_paragraph.clear();
                        },
                        b"w:t" => {
                            // Text content
                            let text = Self::extract_text(&mut reader)?;
                            current_paragraph.push_str(&text);
                        },
                        _ => {}
                    }
                },
                Ok(Event::End(ref e)) => {
                    if e.name().as_ref() == b"w:p" {
                        // End of paragraph - process it
                        if !current_paragraph.trim().is_empty() {
                            let section = Self::process_paragraph(
                                &current_paragraph, 
                                styles,
                                sections.len() as u32
                            )?;
                            sections.push(section);
                        }
                    }
                },
                Ok(Event::Eof) => break,
                Err(e) => return Err(ImportError::XmlParse(e.to_string())),
                _ => {}
            }
        }
        
        Ok(sections)
    }
    
    fn detect_content_type(text: &str, level: u32) -> DetectedContentType {
        let text_lower = text.to_lowercase();
        
        if text_lower.contains("learning objective") || 
           text_lower.contains("objective") && level <= 2 {
            DetectedContentType::LearningObjectives
        } else if text_lower.contains("quiz") || 
                  text_lower.contains("assessment") ||
                  text_lower.contains("question") {
            DetectedContentType::Assessment
        } else if text_lower.contains("outline") ||
                  text_lower.contains("agenda") {
            DetectedContentType::ContentOutline
        } else if text_lower.contains("instruction") ||
                  text_lower.contains("direction") {
            DetectedContentType::Instructions
        } else {
            DetectedContentType::GeneralContent
        }
    }
}
```

### 1.1.4 Markdown and Text Import

**Technical Implementation**:

```rust
// File: src-tauri/src/import/markdown.rs
use pulldown_cmark::{Parser, Event, Tag, HeadingLevel};

#[derive(Debug, Clone)]
pub struct MarkdownDocument {
    pub frontmatter: Option<FrontMatter>,
    pub sections: Vec<MarkdownSection>,
    pub metadata: DocumentMetadata,
}

#[derive(Debug, Clone)]
pub struct FrontMatter {
    pub title: Option<String>,
    pub author: Option<String>,
    pub subject: Option<String>,
    pub learning_objectives: Option<Vec<String>>,
    pub custom_fields: HashMap<String, String>,
}

pub struct MarkdownParser;

impl MarkdownParser {
    pub fn parse(file_path: &Path) -> Result<MarkdownDocument, ImportError> {
        let content = std::fs::read_to_string(file_path)?;
        
        // 1. Extract frontmatter if present
        let (frontmatter, content_body) = Self::extract_frontmatter(&content)?;
        
        // 2. Parse markdown content
        let parser = Parser::new(&content_body);
        let sections = Self::parse_markdown_structure(parser)?;
        
        // 3. Generate metadata
        let metadata = Self::generate_metadata(&frontmatter, &sections, file_path)?;
        
        Ok(MarkdownDocument {
            frontmatter,
            sections,
            metadata,
        })
    }
    
    fn extract_frontmatter(content: &str) -> Result<(Option<FrontMatter>, String), ImportError> {
        if content.starts_with("---\n") {
            if let Some(end_pos) = content[4..].find("\n---\n") {
                let frontmatter_text = &content[4..end_pos + 4];
                let content_body = content[end_pos + 8..].to_string();
                
                let frontmatter: FrontMatter = serde_yaml::from_str(frontmatter_text)
                    .map_err(|e| ImportError::FrontMatterParse(e.to_string()))?;
                
                return Ok((Some(frontmatter), content_body));
            }
        }
        Ok((None, content.to_string()))
    }
    
    fn parse_markdown_structure(parser: Parser) -> Result<Vec<MarkdownSection>, ImportError> {
        let mut sections = Vec::new();
        let mut current_section = None;
        let mut current_text = String::new();
        
        for event in parser {
            match event {
                Event::Start(Tag::Heading(level, _, _)) => {
                    // Save previous section if exists
                    if let Some(section) = current_section.take() {
                        sections.push(section);
                    }
                    
                    current_section = Some(MarkdownSection {
                        heading: String::new(),
                        level: level as u32,
                        content: String::new(),
                        content_type: DetectedContentType::GeneralContent,
                    });
                },
                Event::Text(text) => {
                    current_text.push_str(&text);
                },
                Event::End(Tag::Heading(_, _, _)) => {
                    if let Some(ref mut section) = current_section {
                        section.heading = current_text.clone();
                        section.content_type = Self::detect_content_type(&current_text, section.level);
                    }
                    current_text.clear();
                },
                Event::End(Tag::Paragraph) => {
                    if let Some(ref mut section) = current_section {
                        section.content.push_str(&current_text);
                        section.content.push('\n');
                    }
                    current_text.clear();
                },
                _ => {}
            }
        }
        
        // Add final section
        if let Some(section) = current_section {
            sections.push(section);
        }
        
        Ok(sections)
    }
}
```

## 1.2 Import Content Analysis

### 1.2.1 Content Type Detection Engine

```rust
// File: src-tauri/src/import/analysis.rs
use regex::Regex;

pub struct ContentAnalyzer;

impl ContentAnalyzer {
    pub fn analyze_document<T: ImportedDocument>(document: &T) -> AnalysisResult {
        AnalysisResult {
            detected_pedagogy: Self::detect_pedagogical_approach(document),
            learning_objectives: Self::extract_learning_objectives(document),
            content_structure: Self::analyze_structure(document),
            quality_metrics: Self::assess_quality(document),
            improvement_areas: Self::identify_improvements(document),
        }
    }
    
    fn detect_pedagogical_approach<T: ImportedDocument>(document: &T) -> PedagogicalApproach {
        let content = document.get_all_text();
        let indicators = vec![
            (PedagogicalApproach::Bloom, vec!["remember", "understand", "apply", "analyze", "evaluate", "create"]),
            (PedagogicalApproach::Gagne, vec!["attention", "objective", "recall", "stimulus", "guidance"]),
            (PedagogicalApproach::Constructivist, vec!["build", "construct", "experience", "reflect"]),
        ];
        
        let mut scores = HashMap::new();
        for (approach, keywords) in indicators {
            let score = keywords.iter()
                .map(|keyword| content.matches(keyword).count())
                .sum::<usize>();
            scores.insert(approach, score);
        }
        
        scores.into_iter()
            .max_by_key(|(_, score)| *score)
            .map(|(approach, _)| approach)
            .unwrap_or(PedagogicalApproach::Traditional)
    }
    
    fn extract_learning_objectives<T: ImportedDocument>(document: &T) -> Vec<LearningObjective> {
        let objective_patterns = vec![
            Regex::new(r"(?i)(?:by the end|after|upon completion).*?(?:student|learner)s?\s+(?:will|should|can)\s+(.+?)(?:\.|$)").unwrap(),
            Regex::new(r"(?i)(?:objective|goal|aim)s?:?\s*(.+?)(?:\n|$)").unwrap(),
            Regex::new(r"(?i)students?\s+(?:will|should|can)\s+(.+?)(?:\.|$)").unwrap(),
        ];
        
        let mut objectives = Vec::new();
        let content = document.get_all_text();
        
        for pattern in objective_patterns {
            for capture in pattern.captures_iter(&content) {
                if let Some(objective_text) = capture.get(1) {
                    let objective = LearningObjective {
                        text: objective_text.as_str().trim().to_string(),
                        bloom_level: Self::classify_bloom_level(objective_text.as_str()),
                        confidence: Self::calculate_confidence(&objective_text.as_str()),
                    };
                    objectives.push(objective);
                }
            }
        }
        
        objectives
    }
    
    fn assess_quality<T: ImportedDocument>(document: &T) -> QualityMetrics {
        let content = document.get_all_text();
        let word_count = content.split_whitespace().count();
        
        QualityMetrics {
            readability_score: Self::calculate_readability(&content),
            structure_score: Self::assess_structure(document),
            engagement_score: Self::assess_engagement(&content),
            accessibility_score: Self::assess_accessibility(document),
            completeness_score: Self::assess_completeness(document),
            word_count,
        }
    }
}
```

### 1.2.2 Learning Objective Extraction

```rust
// File: src-tauri/src/import/objectives.rs
#[derive(Debug, Clone)]
pub struct LearningObjective {
    pub text: String,
    pub bloom_level: BloomLevel,
    pub action_verb: String,
    pub content_area: String,
    pub condition: Option<String>,
    pub criteria: Option<String>,
    pub confidence: f64,
}

#[derive(Debug, Clone)]
pub enum BloomLevel {
    Remember,
    Understand,
    Apply,
    Analyze,
    Evaluate,
    Create,
    Unknown,
}

pub struct ObjectiveExtractor;

impl ObjectiveExtractor {
    fn classify_bloom_level(objective_text: &str) -> BloomLevel {
        let bloom_verbs = hashmap! {
            BloomLevel::Remember => vec!["list", "name", "identify", "describe", "retrieve", "recognize"],
            BloomLevel::Understand => vec!["explain", "interpret", "summarize", "paraphrase", "classify"],
            BloomLevel::Apply => vec!["apply", "execute", "implement", "demonstrate", "use"],
            BloomLevel::Analyze => vec!["analyze", "differentiate", "organize", "compare", "contrast"],
            BloomLevel::Evaluate => vec!["evaluate", "critique", "judge", "defend", "support"],
            BloomLevel::Create => vec!["create", "design", "construct", "develop", "formulate"],
        };
        
        let text_lower = objective_text.to_lowercase();
        
        for (level, verbs) in bloom_verbs {
            for verb in verbs {
                if text_lower.contains(verb) {
                    return level;
                }
            }
        }
        
        BloomLevel::Unknown
    }
    
    fn extract_components(objective_text: &str) -> (String, String, Option<String>, Option<String>) {
        // Parse: "[Condition] Student will [action verb] [content] [criteria]"
        let condition_pattern = Regex::new(r"^([^,]+),\s*").unwrap();
        let main_pattern = Regex::new(r"(?:student|learner)s?\s+(?:will|should|can)\s+(\w+)\s+(.+?)(?:\s+(?:with|to|at)\s+(.+?))?(?:\.|$)").unwrap();
        
        let (text_without_condition, condition) = if let Some(cap) = condition_pattern.captures(objective_text) {
            (objective_text[cap.get(0).unwrap().end()..].to_string(), Some(cap[1].to_string()))
        } else {
            (objective_text.to_string(), None)
        };
        
        if let Some(cap) = main_pattern.captures(&text_without_condition) {
            let action_verb = cap[1].to_string();
            let content = cap[2].to_string();
            let criteria = cap.get(3).map(|m| m.as_str().to_string());
            
            (action_verb, content, condition, criteria)
        } else {
            ("understand".to_string(), objective_text.to_string(), condition, None)
        }
    }
}
```

## 1.3 Basic Curation Workflow

### 1.3.1 Import & Improve UI Flow

```typescript
// File: src/components/ImportImproveWorkflow.tsx
interface ImportImproveWorkflowProps {
  onComplete: (result: CurationResult) => void;
}

export const ImportImproveWorkflow: React.FC<ImportImproveWorkflowProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState<ImportStep>('select-file');
  const [importedContent, setImportedContent] = useState<ImportedDocument | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [improvements, setImprovements] = useState<Improvement[]>([]);

  const steps: ImportStep[] = [
    'select-file',
    'preview-content',
    'analyze-content',
    'review-suggestions',
    'apply-improvements',
    'finalize'
  ];

  const handleFileSelect = async (file: File) => {
    try {
      const result = await invoke<ImportedDocument>('import_document', { filePath: file.path });
      setImportedContent(result);
      setCurrentStep('preview-content');
    } catch (error) {
      console.error('Import failed:', error);
    }
  };

  const handleAnalyze = async () => {
    if (!importedContent) return;
    
    setCurrentStep('analyze-content');
    try {
      const analysis = await invoke<AnalysisResult>('analyze_content', { 
        document: importedContent 
      });
      setAnalysisResult(analysis);
      
      const suggestions = await invoke<Improvement[]>('generate_improvements', {
        analysis,
        preferences: userPreferences
      });
      setImprovements(suggestions);
      setCurrentStep('review-suggestions');
    } catch (error) {
      console.error('Analysis failed:', error);
    }
  };

  return (
    <div className="import-improve-workflow">
      <ProgressIndicator steps={steps} currentStep={currentStep} />
      
      {currentStep === 'select-file' && (
        <FileSelector 
          onFileSelect={handleFileSelect}
          acceptedTypes={['.pptx', '.docx', '.md', '.txt']}
        />
      )}
      
      {currentStep === 'preview-content' && importedContent && (
        <ContentPreview 
          content={importedContent}
          onContinue={handleAnalyze}
          onBack={() => setCurrentStep('select-file')}
        />
      )}
      
      {currentStep === 'analyze-content' && (
        <AnalysisProgress />
      )}
      
      {currentStep === 'review-suggestions' && analysisResult && (
        <SuggestionReview
          analysis={analysisResult}
          improvements={improvements}
          onApplySelected={(selectedImprovements) => {
            setCurrentStep('apply-improvements');
            applyImprovements(selectedImprovements);
          }}
        />
      )}
      
      {currentStep === 'apply-improvements' && (
        <ImprovementProgress />
      )}
      
      {currentStep === 'finalize' && (
        <CurationSummary 
          originalContent={importedContent}
          improvedContent={improvedContent}
          appliedImprovements={appliedImprovements}
          onComplete={onComplete}
        />
      )}
    </div>
  );
};
```

### 1.3.2 Side-by-Side Comparison Component

```typescript
// File: src/components/ContentComparison.tsx
interface ContentComparisonProps {
  original: ImportedDocument;
  improved: GeneratedContent;
  improvements: AppliedImprovement[];
}

export const ContentComparison: React.FC<ContentComparisonProps> = ({
  original,
  improved,
  improvements
}) => {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'overlay' | 'diff'>('side-by-side');
  const [highlightChanges, setHighlightChanges] = useState(true);

  return (
    <div className="content-comparison">
      <div className="comparison-controls">
        <ViewModeSelector value={viewMode} onChange={setViewMode} />
        <Toggle
          label="Highlight Changes"
          checked={highlightChanges}
          onChange={setHighlightChanges}
        />
      </div>

      <div className={`comparison-view ${viewMode}`}>
        <div className="original-content">
          <h3>Original Content</h3>
          <ContentRenderer 
            content={original} 
            highlightAreas={highlightChanges ? improvements.map(i => i.originalSpan) : []}
          />
        </div>

        <div className="improved-content">
          <h3>Improved Content</h3>
          <ContentRenderer 
            content={improved} 
            highlightAreas={highlightChanges ? improvements.map(i => i.improvedSpan) : []}
          />
        </div>
      </div>

      <div className="improvement-summary">
        <h4>Applied Improvements</h4>
        <ImprovementList improvements={improvements} />
      </div>
    </div>
  );
};
```

## Backend Command Handlers

### 1.3.3 Tauri Commands for Import/Curation

```rust
// File: src-tauri/src/commands/import.rs
use crate::import::{ImportedDocument, AnalysisResult, Improvement};

#[tauri::command]
pub async fn import_document(file_path: String) -> Result<ImportedDocument, String> {
    let path = Path::new(&file_path);
    let extension = path.extension()
        .and_then(|ext| ext.to_str())
        .ok_or("Invalid file extension")?;

    match extension.to_lowercase().as_str() {
        "pptx" => {
            PowerPointParser::parse(path)
                .map(ImportedDocument::PowerPoint)
                .map_err(|e| e.to_string())
        },
        "docx" => {
            WordParser::parse(path)
                .map(ImportedDocument::Word)
                .map_err(|e| e.to_string())
        },
        "md" => {
            MarkdownParser::parse(path)
                .map(ImportedDocument::Markdown)
                .map_err(|e| e.to_string())
        },
        "txt" => {
            TextParser::parse(path)
                .map(ImportedDocument::Text)
                .map_err(|e| e.to_string())
        },
        _ => Err(format!("Unsupported file type: {}", extension))
    }
}

#[tauri::command]
pub async fn analyze_content(document: ImportedDocument) -> Result<AnalysisResult, String> {
    ContentAnalyzer::analyze_document(&document)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn generate_improvements(
    analysis: AnalysisResult,
    preferences: UserPreferences
) -> Result<Vec<Improvement>, String> {
    ImprovementEngine::generate_suggestions(&analysis, &preferences)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn apply_improvements(
    document: ImportedDocument,
    improvements: Vec<Improvement>
) -> Result<GeneratedContent, String> {
    CurationEngine::apply_improvements(document, improvements)
        .await
        .map_err(|e| e.to_string())
}
```

## Error Handling and Validation

### 1.3.4 Comprehensive Error Types

```rust
// File: src-tauri/src/import/errors.rs
#[derive(Debug, thiserror::Error)]
pub enum ImportError {
    #[error("File not found: {0}")]
    FileNotFound(String),
    
    #[error("Unsupported file format: {0}")]
    UnsupportedFormat(String),
    
    #[error("XML parsing error: {0}")]
    XmlParse(String),
    
    #[error("ZIP extraction error: {0}")]
    ZipExtraction(String),
    
    #[error("Frontmatter parsing error: {0}")]
    FrontMatterParse(String),
    
    #[error("Content analysis error: {0}")]
    AnalysisError(String),
    
    #[error("File too large: {size} bytes (max: {max} bytes)")]
    FileTooLarge { size: u64, max: u64 },
    
    #[error("Corrupted file: {0}")]
    CorruptedFile(String),
    
    #[error("Permission denied: {0}")]
    PermissionDenied(String),
}

impl From<ImportError> for String {
    fn from(error: ImportError) -> Self {
        error.to_string()
    }
}
```

## Testing Strategy

### 1.3.5 Test Files and Cases

```rust
// File: src-tauri/src/import/tests.rs
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[tokio::test]
    async fn test_powerpoint_import() {
        let test_file = "test_files/sample_presentation.pptx";
        let result = PowerPointParser::parse(Path::new(test_file)).unwrap();
        
        assert!(result.slides.len() > 0);
        assert!(!result.title.is_empty());
        assert!(result.slides[0].content.len() > 0);
    }

    #[tokio::test]
    async fn test_markdown_with_frontmatter() {
        let content = r#"---
title: "Test Course"
author: "Test Author"
learning_objectives:
  - "Students will understand basic concepts"
  - "Students will apply knowledge"
---

# Introduction

This is a test course.

## Learning Objectives

Students will be able to:
- Understand basic concepts
- Apply knowledge in practice
"#;
        
        let temp_dir = TempDir::new().unwrap();
        let file_path = temp_dir.path().join("test.md");
        std::fs::write(&file_path, content).unwrap();
        
        let result = MarkdownParser::parse(&file_path).unwrap();
        
        assert!(result.frontmatter.is_some());
        assert_eq!(result.frontmatter.as_ref().unwrap().title, Some("Test Course".to_string()));
        assert_eq!(result.sections.len(), 2);
    }

    #[tokio::test]
    async fn test_learning_objective_extraction() {
        let content = "Students will be able to analyze complex problems and create solutions.";
        let objectives = ObjectiveExtractor::extract_from_text(content);
        
        assert_eq!(objectives.len(), 1);
        assert_eq!(objectives[0].bloom_level, BloomLevel::Create);
    }
}
```

## Configuration and Settings

### 1.3.6 Import Settings

```rust
// File: src-tauri/src/import/config.rs
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportConfig {
    pub max_file_size_mb: u64,
    pub supported_formats: Vec<String>,
    pub auto_analyze: bool,
    pub extract_images: bool,
    pub preserve_formatting: bool,
    pub objective_extraction: ObjectiveExtractionConfig,
    pub quality_thresholds: QualityThresholds,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectiveExtractionConfig {
    pub enabled: bool,
    pub confidence_threshold: f64,
    pub bloom_classification: bool,
    pub custom_patterns: Vec<String>,
}

impl Default for ImportConfig {
    fn default() -> Self {
        Self {
            max_file_size_mb: 10,
            supported_formats: vec![
                "pptx".to_string(),
                "docx".to_string(), 
                "md".to_string(),
                "txt".to_string()
            ],
            auto_analyze: true,
            extract_images: false, // Phase 2 feature
            preserve_formatting: true,
            objective_extraction: ObjectiveExtractionConfig {
                enabled: true,
                confidence_threshold: 0.7,
                bloom_classification: true,
                custom_patterns: vec![],
            },
            quality_thresholds: QualityThresholds::default(),
        }
    }
}
```

## Implementation Timeline

### Week 1: Core Infrastructure
- **Days 1-2**: Add dependencies, set up project structure
- **Days 3-4**: Implement PowerPoint parser with basic functionality  
- **Days 5-7**: Implement Word parser and test with sample files

### Week 2: Analysis and UI
- **Days 1-2**: Build content analysis engine
- **Days 3-4**: Create import workflow UI components
- **Days 5-7**: Implement improvement suggestion system

### Week 3: Integration and Testing
- **Days 1-2**: Connect frontend and backend
- **Days 3-4**: Comprehensive testing with various file types
- **Days 5-7**: Error handling, edge cases, and documentation

## Success Criteria

1. **Import Success Rate**: 90% of common PowerPoint and Word files import successfully
2. **Analysis Accuracy**: Learning objectives detected with 80% accuracy
3. **UI Responsiveness**: Import workflow completes in under 30 seconds for typical files
4. **Error Handling**: Graceful failure with helpful error messages
5. **Test Coverage**: 85% code coverage for import functionality

## Next Phase Preparation

Phase 1 establishes the foundation for:
- **Phase 2**: Enhanced content generation with imported context
- **Phase 3**: Reference material integration using similar parsing techniques
- **Phase 4**: Advanced curation with the import analysis as baseline

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Create detailed Phase 1 technical specifications", "status": "completed", "priority": "high", "id": "1"}]