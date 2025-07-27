use super::{ExportFormat, ExportOptions, ExportResult, FormatConverter, BrandingOptions};
use crate::content::GeneratedContent;
use anyhow::{Result, Context};
use std::fs;
use std::io::{Write, Cursor};
use chrono::Utc;
use zip::{ZipWriter, write::FileOptions, CompressionMethod};

pub struct WordConverter;

impl WordConverter {
    pub fn new() -> Self {
        Self
    }

    fn content_to_docx(&self, contents: &[GeneratedContent], options: &ExportOptions) -> Result<Vec<u8>> {
        let mut zip_buffer = Vec::new();
        {
            let mut zip = ZipWriter::new(Cursor::new(&mut zip_buffer));
            
            // Create the basic Word document structure
            self.add_docx_structure(&mut zip, contents, options)?;
        }
        
        Ok(zip_buffer)
    }
    
    fn add_docx_structure(
        &self,
        zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>,
        contents: &[GeneratedContent],
        options: &ExportOptions
    ) -> Result<()> {
        // Add [Content_Types].xml
        self.add_content_types(zip)?;
        
        // Add _rels/.rels
        self.add_main_rels(zip)?;
        
        // Add app.xml and core.xml
        self.add_app_properties(zip)?;
        self.add_core_properties(zip, contents)?;
        
        // Add document.xml
        self.add_document(zip, contents, options)?;
        
        // Add document.xml.rels
        self.add_document_rels(zip)?;
        
        // Add styles.xml with branding
        self.add_styles(zip, &options.branding_options)?;
        
        // Add settings.xml
        self.add_settings(zip)?;
        
        // Add theme with branding
        self.add_theme(zip, &options.branding_options)?;
        
        // Add font table
        self.add_font_table(zip, &options.branding_options)?;
        
        Ok(())
    }
    
    fn add_content_types(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>) -> Result<()> {
        let content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
    <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
    <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
    <Override PartName="/word/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
    <Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>
    <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
    <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"#;
        
        self.add_file_to_zip(zip, "[Content_Types].xml", content)?;
        Ok(())
    }
    
    fn add_main_rels(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>) -> Result<()> {
        let content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
    <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"#;
        
        self.add_file_to_zip(zip, "_rels/.rels", content)?;
        Ok(())
    }
    
    fn add_app_properties(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>) -> Result<()> {
        let content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
    <Application>Curriculum Curator</Application>
    <DocSecurity>0</DocSecurity>
    <Lines>1</Lines>
    <Paragraphs>1</Paragraphs>
    <ScaleCrop>false</ScaleCrop>
    <Company>Educational Technology</Company>
    <LinksUpToDate>false</LinksUpToDate>
    <SharedDoc>false</SharedDoc>
    <HyperlinksChanged>false</HyperlinksChanged>
    <AppVersion>1.0</AppVersion>
</Properties>"#;
        
        self.add_file_to_zip(zip, "docProps/app.xml", content)?;
        Ok(())
    }
    
    fn add_core_properties(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>, contents: &[GeneratedContent]) -> Result<()> {
        let now = Utc::now().to_rfc3339();
        let title = if contents.len() == 1 {
            &contents[0].title
        } else {
            "Curriculum Content Export"
        };
        
        let content = format!(r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <dc:title>{}</dc:title>
    <dc:creator>Curriculum Curator</dc:creator>
    <cp:lastModifiedBy>Curriculum Curator</cp:lastModifiedBy>
    <dcterms:created xsi:type="dcterms:W3CDTF">{}</dcterms:created>
    <dcterms:modified xsi:type="dcterms:W3CDTF">{}</dcterms:modified>
</cp:coreProperties>"#, self.escape_xml(title), now, now);
        
        self.add_file_to_zip(zip, "docProps/core.xml", &content)?;
        Ok(())
    }
    
    fn add_document(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>, contents: &[GeneratedContent], options: &ExportOptions) -> Result<()> {
        let mut document_content = String::new();
        
        // Add document header
        document_content.push_str(r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <w:body>"#);
        
        // Add title page if multiple contents or if branding is enabled
        if contents.len() > 1 || options.branding_options.is_some() {
            self.add_title_page(&mut document_content, contents, &options.branding_options)?;
        }
        
        // Add each content item
        for (i, content) in contents.iter().enumerate() {
            if i > 0 {
                // Add page break between content items
                document_content.push_str(r#"
        <w:p>
            <w:r>
                <w:br w:type="page"/>
            </w:r>
        </w:p>"#);
            }
            
            self.add_content_to_document(&mut document_content, content)?;
        }
        
        // Add document footer
        document_content.push_str(r#"
    </w:body>
</w:document>"#);
        
        self.add_file_to_zip(zip, "word/document.xml", &document_content)?;
        Ok(())
    }
    
    fn add_title_page(&self, document: &mut String, contents: &[GeneratedContent], branding: &Option<BrandingOptions>) -> Result<()> {
        let title = if contents.len() == 1 {
            &contents[0].title
        } else {
            "Curriculum Content Export"
        };
        
        let institution = branding.as_ref()
            .and_then(|b| b.institution_name.as_ref())
            .map(|s| s.as_str())
            .unwrap_or("Educational Institution");
        
        let formatted_date = Utc::now().format("%B %d, %Y").to_string();
        
        document.push_str(&format!(r#"
        <w:p>
            <w:pPr>
                <w:jc w:val="center"/>
                <w:spacing w:after="480"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:b/>
                    <w:sz w:val="36"/>
                    <w:color w:val="2F5233"/>
                </w:rPr>
                <w:t>{}</w:t>
            </w:r>
        </w:p>
        
        <w:p>
            <w:pPr>
                <w:jc w:val="center"/>
                <w:spacing w:after="240"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:sz w:val="24"/>
                    <w:color w:val="595959"/>
                </w:rPr>
                <w:t>{}</w:t>
            </w:r>
        </w:p>
        
        <w:p>
            <w:pPr>
                <w:jc w:val="center"/>
                <w:spacing w:after="960"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:sz w:val="20"/>
                    <w:color w:val="808080"/>
                </w:rPr>
                <w:t>{}</w:t>
            </w:r>
        </w:p>
        
        <w:p>
            <w:r>
                <w:br w:type="page"/>
            </w:r>
        </w:p>"#, 
            self.escape_xml(title),
            self.escape_xml(institution),
            formatted_date
        ));
        
        Ok(())
    }
    
    fn add_content_to_document(&self, document: &mut String, content: &GeneratedContent) -> Result<()> {
        // Add content title
        document.push_str(&format!(r#"
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
                <w:spacing w:after="240"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:b/>
                    <w:sz w:val="28"/>
                    <w:color w:val="2F5233"/>
                </w:rPr>
                <w:t>{}</w:t>
            </w:r>
        </w:p>"#, self.escape_xml(&content.title)));
        
        // Add content type badge
        let content_type_label = self.format_content_type(&content.content_type);
        document.push_str(&format!(r#"
        <w:p>
            <w:pPr>
                <w:spacing w:after="120"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:sz w:val="18"/>
                    <w:color w:val="4F81BD"/>
                    <w:b/>
                </w:rPr>
                <w:t>{}</w:t>
            </w:r>
        </w:p>"#, content_type_label));
        
        // Add metadata if available
        document.push_str(&format!(r#"
        <w:p>
            <w:pPr>
                <w:spacing w:after="240"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:sz w:val="16"/>
                    <w:color w:val="808080"/>
                    <w:i/>
                </w:rPr>
                <w:t>Duration: {} | Difficulty: {} | Words: {}</w:t>
            </w:r>
        </w:p>"#, 
            content.metadata.estimated_duration,
            content.metadata.difficulty_level,
            content.metadata.word_count
        ));
        
        // Process content based on type
        match content.content_type {
            crate::content::ContentType::Slides => {
                self.add_slides_content(document, &content.content)?;
            }
            _ => {
                self.add_regular_content(document, &content.content)?;
            }
        }
        
        Ok(())
    }
    
    fn add_slides_content(&self, document: &mut String, content: &str) -> Result<()> {
        let slides: Vec<&str> = content.split("---SLIDE---").collect();
        
        for (i, slide_content) in slides.iter().enumerate() {
            if slide_content.trim().is_empty() {
                continue;
            }
            
            if i > 0 {
                // Add page break between slides
                document.push_str(r#"
        <w:p>
            <w:r>
                <w:br w:type="page"/>
            </w:r>
        </w:p>"#);
            }
            
            // Add slide number
            document.push_str(&format!(r#"
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading2"/>
                <w:spacing w:after="120"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:b/>
                    <w:sz w:val="24"/>
                    <w:color w:val="4F81BD"/>
                </w:rPr>
                <w:t>Slide {}</w:t>
            </w:r>
        </w:p>"#, i + 1));
            
            self.add_formatted_text(document, slide_content.trim())?;
        }
        
        Ok(())
    }
    
    fn add_regular_content(&self, document: &mut String, content: &str) -> Result<()> {
        self.add_formatted_text(document, content)?;
        Ok(())
    }
    
    fn add_formatted_text(&self, document: &mut String, text: &str) -> Result<()> {
        let lines: Vec<&str> = text.lines().collect();
        let mut in_list = false;
        
        for line in lines {
            let trimmed = line.trim();
            
            if trimmed.is_empty() {
                // Add empty paragraph
                document.push_str(r#"
        <w:p>
            <w:pPr>
                <w:spacing w:after="120"/>
            </w:pPr>
        </w:p>"#);
                continue;
            }
            
            if trimmed.starts_with("# ") {
                // Heading 1
                let heading_text = trimmed.trim_start_matches("# ");
                document.push_str(&format!(r#"
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading2"/>
                <w:spacing w:after="180"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:b/>
                    <w:sz w:val="24"/>
                    <w:color w:val="2F5233"/>
                </w:rPr>
                <w:t>{}</w:t>
            </w:r>
        </w:p>"#, self.escape_xml(heading_text)));
            } else if trimmed.starts_with("## ") {
                // Heading 2
                let heading_text = trimmed.trim_start_matches("## ");
                document.push_str(&format!(r#"
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading3"/>
                <w:spacing w:after="140"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:b/>
                    <w:sz w:val="20"/>
                    <w:color w:val="4F81BD"/>
                </w:rPr>
                <w:t>{}</w:t>
            </w:r>
        </w:p>"#, self.escape_xml(heading_text)));
            } else if trimmed.starts_with("- ") || trimmed.starts_with("* ") {
                // Bullet point
                let bullet_text = trimmed.trim_start_matches("- ").trim_start_matches("* ");
                in_list = true;
                document.push_str(&format!(r#"
        <w:p>
            <w:pPr>
                <w:pStyle w:val="ListParagraph"/>
                <w:numPr>
                    <w:ilvl w:val="0"/>
                    <w:numId w:val="1"/>
                </w:numPr>
                <w:spacing w:after="100"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:sz w:val="22"/>
                </w:rPr>
                <w:t>{}</w:t>
            </w:r>
        </w:p>"#, self.escape_xml(bullet_text)));
            } else {
                // Regular paragraph
                if in_list {
                    in_list = false;
                }
                document.push_str(&format!(r#"
        <w:p>
            <w:pPr>
                <w:spacing w:after="140"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:sz w:val="22"/>
                </w:rPr>
                <w:t>{}</w:t>
            </w:r>
        </w:p>"#, self.escape_xml(trimmed)));
            }
        }
        
        Ok(())
    }
    
    fn add_document_rels(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>) -> Result<()> {
        let content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
    <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
    <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>
</Relationships>"#;
        
        self.add_file_to_zip(zip, "word/_rels/document.xml.rels", content)?;
        Ok(())
    }
    
    fn add_styles(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>, branding: &Option<BrandingOptions>) -> Result<()> {
        let (heading_font, body_font) = if let Some(branding) = branding {
            (
                branding.fonts.heading.split(',').next().unwrap_or("Arial").trim().trim_matches('"'),
                branding.fonts.body.split(',').next().unwrap_or("Arial").trim().trim_matches('"')
            )
        } else {
            ("Arial", "Arial")
        };
        
        let primary_color = branding.as_ref()
            .map(|b| self.hex_to_rgb_hex(&b.colors.primary))
            .unwrap_or_else(|| "2F5233".to_string());
        
        let content = format!(r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:docDefaults>
        <w:rPrDefault>
            <w:rPr>
                <w:rFonts w:ascii="{}" w:eastAsia="{}" w:hAnsi="{}" w:cs="Times New Roman"/>
                <w:sz w:val="22"/>
                <w:szCs w:val="22"/>
                <w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="ar-SA"/>
            </w:rPr>
        </w:rPrDefault>
        <w:pPrDefault>
            <w:pPr>
                <w:spacing w:after="160" w:line="276" w:lineRule="auto"/>
            </w:pPr>
        </w:pPrDefault>
    </w:docDefaults>
    
    <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
        <w:name w:val="Normal"/>
        <w:qFormat/>
    </w:style>
    
    <w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont">
        <w:name w:val="Default Paragraph Font"/>
        <w:uiPriority w:val="1"/>
        <w:semiHidden/>
        <w:unhideWhenUsed/>
    </w:style>
    
    <w:style w:type="table" w:default="1" w:styleId="TableNormal">
        <w:name w:val="Normal Table"/>
        <w:uiPriority w:val="99"/>
        <w:semiHidden/>
        <w:unhideWhenUsed/>
        <w:tblPr>
            <w:tblInd w:w="0" w:type="dxa"/>
            <w:tblCellMar>
                <w:top w:w="0" w:type="dxa"/>
                <w:left w:w="108" w:type="dxa"/>
                <w:bottom w:w="0" w:type="dxa"/>
                <w:right w:w="108" w:type="dxa"/>
            </w:tblCellMar>
        </w:tblPr>
    </w:style>
    
    <w:style w:type="numbering" w:default="1" w:styleId="NoList">
        <w:name w:val="No List"/>
        <w:uiPriority w:val="99"/>
        <w:semiHidden/>
        <w:unhideWhenUsed/>
    </w:style>
    
    <w:style w:type="paragraph" w:styleId="Heading1">
        <w:name w:val="heading 1"/>
        <w:basedOn w:val="Normal"/>
        <w:next w:val="Normal"/>
        <w:link w:val="Heading1Char"/>
        <w:uiPriority w:val="9"/>
        <w:qFormat/>
        <w:pPr>
            <w:keepNext/>
            <w:keepLines/>
            <w:spacing w:before="240" w:after="0"/>
            <w:outlineLvl w:val="0"/>
        </w:pPr>
        <w:rPr>
            <w:rFonts w:asciiTheme="majorHAnsi" w:eastAsiaTheme="majorEastAsia" w:hAnsiTheme="majorHAnsi" w:cstheme="majorBidi"/>
            <w:color w:val="{}"/>
            <w:sz w:val="32"/>
            <w:szCs w:val="32"/>
        </w:rPr>
    </w:style>
    
    <w:style w:type="paragraph" w:styleId="Heading2">
        <w:name w:val="heading 2"/>
        <w:basedOn w:val="Normal"/>
        <w:next w:val="Normal"/>
        <w:link w:val="Heading2Char"/>
        <w:uiPriority w:val="9"/>
        <w:unhideWhenUsed/>
        <w:qFormat/>
        <w:pPr>
            <w:keepNext/>
            <w:keepLines/>
            <w:spacing w:before="200" w:after="0"/>
            <w:outlineLvl w:val="1"/>
        </w:pPr>
        <w:rPr>
            <w:rFonts w:asciiTheme="majorHAnsi" w:eastAsiaTheme="majorEastAsia" w:hAnsiTheme="majorHAnsi" w:cstheme="majorBidi"/>
            <w:color w:val="4F81BD"/>
            <w:sz w:val="28"/>
            <w:szCs w:val="28"/>
        </w:rPr>
    </w:style>
    
    <w:style w:type="paragraph" w:styleId="Heading3">
        <w:name w:val="heading 3"/>
        <w:basedOn w:val="Normal"/>
        <w:next w:val="Normal"/>
        <w:link w:val="Heading3Char"/>
        <w:uiPriority w:val="9"/>
        <w:unhideWhenUsed/>
        <w:qFormat/>
        <w:pPr>
            <w:keepNext/>
            <w:keepLines/>
            <w:spacing w:before="160" w:after="0"/>
            <w:outlineLvl w:val="2"/>
        </w:pPr>
        <w:rPr>
            <w:rFonts w:asciiTheme="majorHAnsi" w:eastAsiaTheme="majorEastAsia" w:hAnsiTheme="majorHAnsi" w:cstheme="majorBidi"/>
            <w:color w:val="{}"/>
            <w:sz w:val="24"/>
            <w:szCs w:val="24"/>
        </w:rPr>
    </w:style>
    
    <w:style w:type="paragraph" w:styleId="ListParagraph">
        <w:name w:val="List Paragraph"/>
        <w:basedOn w:val="Normal"/>
        <w:uiPriority w:val="34"/>
        <w:qFormat/>
        <w:pPr>
            <w:ind w:left="720"/>
            <w:contextualSpacing/>
        </w:pPr>
    </w:style>
</w:styles>"#, body_font, body_font, body_font, primary_color, primary_color);
        
        self.add_file_to_zip(zip, "word/styles.xml", &content)?;
        Ok(())
    }
    
    fn add_settings(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>) -> Result<()> {
        let content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:zoom w:percent="100"/>
    <w:proofState w:spelling="clean" w:grammar="clean"/>
    <w:defaultTabStop w:val="708"/>
    <w:characterSpacingControl w:val="doNotCompress"/>
    <w:compat>
        <w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="14"/>
        <w:compatSetting w:name="overrideTableStyleFontSizeAndJustification" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>
        <w:compatSetting w:name="enableOpenTypeFeatures" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>
        <w:compatSetting w:name="doNotFlipMirrorIndents" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>
    </w:compat>
    <w:rsids>
        <w:rsidRoot w:val="00E802B7"/>
        <w:rsid w:val="00E802B7"/>
    </w:rsids>
</w:settings>"#;
        
        self.add_file_to_zip(zip, "word/settings.xml", content)?;
        Ok(())
    }
    
    fn add_theme(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>, branding: &Option<BrandingOptions>) -> Result<()> {
        let (primary_color, secondary_color, accent_color) = if let Some(branding) = branding {
            (
                self.hex_to_rgb_hex(&branding.colors.primary),
                self.hex_to_rgb_hex(&branding.colors.secondary),
                self.hex_to_rgb_hex(&branding.colors.accent)
            )
        } else {
            ("2F5233".to_string(), "4F81BD".to_string(), "F79646".to_string())
        };
        
        let content = format!(r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Curriculum Theme">
    <a:themeElements>
        <a:clrScheme name="Custom">
            <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
            <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
            <a:dk2><a:srgbClr val="1F497D"/></a:dk2>
            <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
            <a:accent1><a:srgbClr val="{}"/></a:accent1>
            <a:accent2><a:srgbClr val="{}"/></a:accent2>
            <a:accent3><a:srgbClr val="{}"/></a:accent3>
            <a:accent4><a:srgbClr val="8064A2"/></a:accent4>
            <a:accent5><a:srgbClr val="4BACC6"/></a:accent5>
            <a:accent6><a:srgbClr val="F366C7"/></a:accent6>
            <a:hlink><a:srgbClr val="0000FF"/></a:hlink>
            <a:folHlink><a:srgbClr val="800080"/></a:folHlink>
        </a:clrScheme>
        <a:fontScheme name="Office">
            <a:majorFont>
                <a:latin typeface="Cambria"/>
                <a:ea typeface=""/>
                <a:cs typeface=""/>
            </a:majorFont>
            <a:minorFont>
                <a:latin typeface="Calibri"/>
                <a:ea typeface=""/>
                <a:cs typeface=""/>
            </a:minorFont>
        </a:fontScheme>
        <a:fmtScheme name="Office">
            <a:fillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:gradFill rotWithShape="1">
                    <a:gsLst>
                        <a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="50000"/><a:satMod val="300000"/></a:schemeClr></a:gs>
                        <a:gs pos="35000"><a:schemeClr val="phClr"><a:tint val="37000"/><a:satMod val="300000"/></a:schemeClr></a:gs>
                        <a:gs pos="100000"><a:schemeClr val="phClr"><a:tint val="15000"/><a:satMod val="350000"/></a:schemeClr></a:gs>
                    </a:gsLst>
                    <a:lin ang="16200000" scaled="1"/>
                </a:gradFill>
                <a:gradFill rotWithShape="1">
                    <a:gsLst>
                        <a:gs pos="0"><a:schemeClr val="phClr"><a:shade val="51000"/><a:satMod val="130000"/></a:schemeClr></a:gs>
                        <a:gs pos="80000"><a:schemeClr val="phClr"><a:shade val="93000"/><a:satMod val="130000"/></a:schemeClr></a:gs>
                        <a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="94000"/><a:satMod val="135000"/></a:schemeClr></a:gs>
                    </a:gsLst>
                    <a:lin ang="16200000" scaled="0"/>
                </a:gradFill>
            </a:fillStyleLst>
            <a:lnStyleLst>
                <a:ln w="9525" cap="flat" cmpd="sng" algn="ctr">
                    <a:solidFill><a:schemeClr val="phClr"><a:shade val="95000"/><a:satMod val="105000"/></a:schemeClr></a:solidFill>
                    <a:prstDash val="solid"/>
                </a:ln>
                <a:ln w="25400" cap="flat" cmpd="sng" algn="ctr">
                    <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                    <a:prstDash val="solid"/>
                </a:ln>
                <a:ln w="38100" cap="flat" cmpd="sng" algn="ctr">
                    <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                    <a:prstDash val="solid"/>
                </a:ln>
            </a:lnStyleLst>
            <a:effectStyleLst>
                <a:effectStyle>
                    <a:effectLst>
                        <a:outerShdw blurRad="40000" dist="20000" dir="5400000" rotWithShape="0">
                            <a:srgbClr val="000000"><a:alpha val="38000"/></a:srgbClr>
                        </a:outerShdw>
                    </a:effectLst>
                </a:effectStyle>
                <a:effectStyle>
                    <a:effectLst>
                        <a:outerShdw blurRad="40000" dist="23000" dir="5400000" rotWithShape="0">
                            <a:srgbClr val="000000"><a:alpha val="35000"/></a:srgbClr>
                        </a:outerShdw>
                    </a:effectLst>
                </a:effectStyle>
                <a:effectStyle>
                    <a:effectLst>
                        <a:outerShdw blurRad="40000" dist="23000" dir="5400000" rotWithShape="0">
                            <a:srgbClr val="000000"><a:alpha val="35000"/></a:srgbClr>
                        </a:outerShdw>
                    </a:effectLst>
                    <a:scene3d>
                        <a:camera prst="orthographicFront">
                            <a:rot lat="0" lon="0" rev="0"/>
                        </a:camera>
                        <a:lightRig rig="threePt" dir="t">
                            <a:rot lat="0" lon="0" rev="1200000"/>
                        </a:lightRig>
                    </a:scene3d>
                    <a:sp3d><a:bevelT w="63500" h="25400"/></a:sp3d>
                </a:effectStyle>
            </a:effectStyleLst>
            <a:bgFillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:gradFill rotWithShape="1">
                    <a:gsLst>
                        <a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="40000"/><a:satMod val="350000"/></a:schemeClr></a:gs>
                        <a:gs pos="40000"><a:schemeClr val="phClr"><a:tint val="45000"/><a:shade val="99000"/><a:satMod val="350000"/></a:schemeClr></a:gs>
                        <a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="20000"/><a:satMod val="255000"/></a:schemeClr></a:gs>
                    </a:gsLst>
                    <a:path path="circle"><a:fillToRect l="50000" t="-80000" r="50000" b="180000"/></a:path>
                </a:gradFill>
                <a:gradFill rotWithShape="1">
                    <a:gsLst>
                        <a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="80000"/><a:satMod val="300000"/></a:schemeClr></a:gs>
                        <a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="30000"/><a:satMod val="200000"/></a:schemeClr></a:gs>
                    </a:gsLst>
                    <a:path path="circle"><a:fillToRect l="50000" t="50000" r="50000" b="50000"/></a:path>
                </a:gradFill>
            </a:bgFillStyleLst>
        </a:fmtScheme>
    </a:themeElements>
</a:theme>"#, primary_color, secondary_color, accent_color);
        
        self.add_file_to_zip(zip, "word/theme/theme1.xml", &content)?;
        Ok(())
    }
    
    fn add_font_table(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>, branding: &Option<BrandingOptions>) -> Result<()> {
        let content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:font w:name="Calibri">
        <w:panose1 w:val="020F0502020204030204"/>
        <w:charset w:val="00"/>
        <w:family w:val="swiss"/>
        <w:pitch w:val="variable"/>
        <w:sig w:usb0="E00002FF" w:usb1="4000ACFF" w:usb2="00000001" w:usb3="00000000" w:csb0="0000019F" w:csb1="00000000"/>
    </w:font>
    <w:font w:name="Times New Roman">
        <w:panose1 w:val="02020603050405020304"/>
        <w:charset w:val="00"/>
        <w:family w:val="roman"/>
        <w:pitch w:val="variable"/>
        <w:sig w:usb0="E0002AFF" w:usb1="C0007841" w:usb2="00000009" w:usb3="00000000" w:csb0="000001FF" w:csb1="00000000"/>
    </w:font>
    <w:font w:name="Arial">
        <w:panose1 w:val="020B0604020202020204"/>
        <w:charset w:val="00"/>
        <w:family w:val="swiss"/>
        <w:pitch w:val="variable"/>
        <w:sig w:usb0="E0002AFF" w:usb1="C0007843" w:usb2="00000009" w:usb3="00000000" w:csb0="000001FF" w:csb1="00000000"/>
    </w:font>
    <w:font w:name="Cambria">
        <w:panose1 w:val="02040503050406030204"/>
        <w:charset w:val="00"/>
        <w:family w:val="roman"/>
        <w:pitch w:val="variable"/>
        <w:sig w:usb0="E00002FF" w:usb1="400004FF" w:usb2="00000000" w:usb3="00000000" w:csb0="0000019F" w:csb1="00000000"/>
    </w:font>
</w:fonts>"#;
        
        self.add_file_to_zip(zip, "word/fontTable.xml", content)?;
        Ok(())
    }
    
    fn format_content_type(&self, content_type: &crate::content::ContentType) -> &'static str {
        match content_type {
            crate::content::ContentType::Slides => "📊 Presentation Slides",
            crate::content::ContentType::InstructorNotes => "📝 Instructor Notes",
            crate::content::ContentType::Worksheet => "📋 Worksheet",
            crate::content::ContentType::Quiz => "❓ Quiz",
            crate::content::ContentType::ActivityGuide => "🎯 Activity Guide",
        }
    }
    
    fn hex_to_rgb_hex(&self, hex_color: &str) -> String {
        // Remove # if present and ensure uppercase, keep only first 6 characters
        hex_color.trim_start_matches('#').chars().take(6).collect::<String>().to_uppercase()
    }
    
    fn escape_xml(&self, text: &str) -> String {
        text.replace('&', "&amp;")
            .replace('<', "&lt;")
            .replace('>', "&gt;")
            .replace('"', "&quot;")
            .replace('\'', "&apos;")
    }
    
    fn add_file_to_zip(
        &self,
        zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>,
        filename: &str,
        content: &str
    ) -> Result<()> {
        let options = FileOptions::default().compression_method(CompressionMethod::Deflated);
        zip.start_file(filename, options)?;
        zip.write_all(content.as_bytes())?;
        Ok(())
    }
}

#[async_trait::async_trait]
impl FormatConverter for WordConverter {
    fn supported_format(&self) -> ExportFormat {
        ExportFormat::Word
    }

    async fn convert(&self, contents: &[GeneratedContent], options: &ExportOptions) -> Result<ExportResult> {
        // Generate the Word document content
        let docx_bytes = self.content_to_docx(contents, options)
            .context("Failed to create Word document")?;

        // Ensure the output directory exists
        if let Some(parent) = options.output_path.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create output directory")?;
        }

        // Write the Word file
        fs::write(&options.output_path, &docx_bytes)
            .context("Failed to write Word file")?;

        // Get file size
        let file_size = fs::metadata(&options.output_path)
            .map(|m| m.len())
            .unwrap_or(0);

        Ok(ExportResult {
            success: true,
            output_path: options.output_path.clone(),
            file_size: Some(file_size),
            error_message: None,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::{ContentType, generator::ContentMetadata};

    fn create_test_content() -> GeneratedContent {
        GeneratedContent {
            content_type: ContentType::InstructorNotes,
            title: "Sample Lesson Plan".to_string(),
            content: "# Introduction\nThis is a sample lesson plan.\n\n## Objectives\n- Learn about topic A\n- Understand concept B\n\n## Activities\nStudents will engage in hands-on learning.".to_string(),
            metadata: ContentMetadata {
                word_count: 25,
                estimated_duration: "45 minutes".to_string(),
                difficulty_level: "Intermediate".to_string(),
            },
        }
    }

    #[tokio::test]
    async fn test_word_conversion() {
        let converter = WordConverter::new();
        let content = create_test_content();
        
        let result = converter.content_to_docx(&[content], &ExportOptions {
            format: ExportFormat::Word,
            output_path: std::path::PathBuf::from("/tmp/test.docx"),
            template_name: None,
            include_metadata: true,
            branding_options: None,
        });
        
        assert!(result.is_ok());
        let docx_bytes = result.unwrap();
        assert!(!docx_bytes.is_empty());
        
        // Check that it starts with ZIP header (PK) - Word documents are ZIP archives
        let zip_header = &docx_bytes[0..2];
        assert_eq!(zip_header, b"PK");
    }

    #[tokio::test]
    async fn test_full_word_export() {
        let converter = WordConverter::new();
        let contents = vec![create_test_content()];
        
        let temp_dir = std::env::temp_dir();
        let output_path = temp_dir.join("test_export.docx");
        
        let options = ExportOptions {
            format: ExportFormat::Word,
            output_path: output_path.clone(),
            template_name: None,
            include_metadata: true,
            branding_options: None,
        };

        let result = converter.convert(&contents, &options).await;
        assert!(result.is_ok());
        
        let export_result = result.unwrap();
        assert!(export_result.success);
        assert!(export_result.file_size.is_some());
        assert!(export_result.file_size.unwrap() > 0);
        
        // Verify file exists and has ZIP header (Word files are ZIP archives)
        assert!(output_path.exists());
        let file_content = std::fs::read(&output_path).unwrap();
        assert!(file_content.starts_with(b"PK"));
        
        // Cleanup
        if output_path.exists() {
            let _ = std::fs::remove_file(output_path);
        }
    }

    #[test]
    fn test_xml_escaping() {
        let converter = WordConverter::new();
        let test_text = "Test & <example> with \"quotes\" and 'apostrophes'";
        let escaped = converter.escape_xml(test_text);
        assert_eq!(escaped, "Test &amp; &lt;example&gt; with &quot;quotes&quot; and &apos;apostrophes&apos;");
    }

    #[test]
    fn test_hex_color_conversion() {
        let converter = WordConverter::new();
        assert_eq!(converter.hex_to_rgb_hex("#FF0000"), "FF0000");
        assert_eq!(converter.hex_to_rgb_hex("00FF00"), "00FF00");
        assert_eq!(converter.hex_to_rgb_hex("#0000ff"), "0000FF");
    }
}