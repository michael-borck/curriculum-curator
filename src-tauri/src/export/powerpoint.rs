use super::{ExportFormat, ExportOptions, ExportResult, FormatConverter, BrandingOptions};
use crate::content::GeneratedContent;
use anyhow::{Result, Context};
use std::fs;
use std::io::{Write, Cursor};
use chrono::Utc;
use zip::{ZipWriter, write::FileOptions, CompressionMethod};

pub struct PowerPointConverter;

impl PowerPointConverter {
    pub fn new() -> Self {
        Self
    }

    fn content_to_pptx(&self, contents: &[GeneratedContent], options: &ExportOptions) -> Result<Vec<u8>> {
        let mut zip_buffer = Vec::new();
        {
            let mut zip = ZipWriter::new(Cursor::new(&mut zip_buffer));
            
            // Create the basic PowerPoint structure
            self.add_pptx_structure(&mut zip, contents, options)?;
        }
        
        Ok(zip_buffer)
    }
    
    fn add_pptx_structure(
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
        
        // Add presentation.xml
        self.add_presentation(zip, contents)?;
        
        // Add presentation rels
        self.add_presentation_rels(zip, contents)?;
        
        // Add theme with branding
        self.add_theme(zip, &options.branding_options)?;
        
        // Add slide master
        self.add_slide_master(zip)?;
        
        // Add slide layouts
        self.add_slide_layouts(zip)?;
        
        // Add slides
        self.add_slides(zip, contents)?;
        
        Ok(())
    }
    
    fn add_content_types(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>) -> Result<()> {
        let content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
    <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
    <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
    <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
    <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
    <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
    <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"#;
        
        self.add_file_to_zip(zip, "[Content_Types].xml", content)?;
        Ok(())
    }
    
    fn add_main_rels(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>) -> Result<()> {
        let content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
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
    <PresentationFormat>On-screen Show (4:3)</PresentationFormat>
    <Slides>1</Slides>
    <Company>Educational Technology</Company>
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
</cp:coreProperties>"#, title, now, now);
        
        self.add_file_to_zip(zip, "docProps/core.xml", &content)?;
        Ok(())
    }
    
    fn add_presentation(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>, contents: &[GeneratedContent]) -> Result<()> {
        let mut slide_ids = String::new();
        let slide_count = self.count_total_slides(contents);
        
        for i in 1..=slide_count {
            slide_ids.push_str(&format!(
                r#"        <p:sldId id="{}" r:id="rId{}"/>"#,
                255 + i,
                i
            ));
            if i < slide_count {
                slide_ids.push('\n');
            }
        }
        
        let content = format!(r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
    <p:sldMasterIdLst>
        <p:sldMasterId id="2147483648" r:id="rId{}"/>
    </p:sldMasterIdLst>
    <p:sldIdLst>
{}
    </p:sldIdLst>
    <p:sldSz cx="9144000" cy="6858000" type="screen4x3"/>
    <p:notesSz cx="6858000" cy="9144000"/>
    <p:defaultTextStyle>
        <a:defPPr>
            <a:defRPr lang="en-US"/>
        </a:defPPr>
    </p:defaultTextStyle>
</p:presentation>"#, slide_count + 1, slide_ids);
        
        self.add_file_to_zip(zip, "ppt/presentation.xml", &content)?;
        Ok(())
    }
    
    fn add_presentation_rels(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>, contents: &[GeneratedContent]) -> Result<()> {
        let mut relationships = String::new();
        let slide_count = self.count_total_slides(contents);
        
        for i in 1..=slide_count {
            relationships.push_str(&format!(
                r#"    <Relationship Id="rId{}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{}.xml"/>"#,
                i, i
            ));
            if i < slide_count {
                relationships.push('\n');
            }
        }
        
        let content = format!(r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{}
    <Relationship Id="rId{}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
    <Relationship Id="rId{}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
</Relationships>"#, relationships, slide_count + 1, slide_count + 2);
        
        self.add_file_to_zip(zip, "ppt/_rels/presentation.xml.rels", &content)?;
        Ok(())
    }
    
    fn hex_to_rgb_hex(&self, hex_color: &str) -> String {
        // Remove # if present and ensure uppercase
        hex_color.trim_start_matches('#').to_uppercase()
    }

    fn add_theme(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>, branding: &Option<BrandingOptions>) -> Result<()> {
        // Determine colors to use (branding or defaults)
        let (primary_color, secondary_color, accent_color) = if let Some(branding) = branding {
            (
                self.hex_to_rgb_hex(&branding.colors.primary),
                self.hex_to_rgb_hex(&branding.colors.secondary),
                self.hex_to_rgb_hex(&branding.colors.accent)
            )
        } else {
            ("4F81BD".to_string(), "1F497D".to_string(), "F79646".to_string())
        };

        let (heading_font, body_font) = if let Some(branding) = branding {
            (
                // Extract just the font family name from CSS font string
                branding.fonts.heading.split(',').next().unwrap_or("Calibri Light").trim().trim_matches('"'),
                branding.fonts.body.split(',').next().unwrap_or("Calibri").trim().trim_matches('"')
            )
        } else {
            ("Calibri Light", "Calibri")
        };

        let content = format!(r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Branded Theme">
    <a:themeElements>
        <a:clrScheme name="Custom">
            <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
            <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
            <a:dk2><a:srgbClr val="{}"/></a:dk2>
            <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
            <a:accent1><a:srgbClr val="{}"/></a:accent1>
            <a:accent2><a:srgbClr val="{}"/></a:accent2>
            <a:accent3><a:srgbClr val="9BBB59"/></a:accent3>
            <a:accent4><a:srgbClr val="8064A2"/></a:accent4>
            <a:accent5><a:srgbClr val="4BACC6"/></a:accent5>
            <a:accent6><a:srgbClr val="F366C7"/></a:accent6>
            <a:hlink><a:srgbClr val="{}"/></a:hlink>
            <a:folHlink><a:srgbClr val="800080"/></a:folHlink>
        </a:clrScheme>
        <a:fontScheme name="Custom">
            <a:majorFont>
                <a:latin typeface="{}"/>
                <a:ea typeface=""/>
                <a:cs typeface=""/>
            </a:majorFont>
            <a:minorFont>
                <a:latin typeface="{}"/>
                <a:ea typeface=""/>
                <a:cs typeface=""/>
            </a:minorFont>
        </a:fontScheme>
        <a:fmtScheme name="Office">
            <a:fillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="50000"/><a:satMod val="300000"/></a:schemeClr></a:gs><a:gs pos="35000"><a:schemeClr val="phClr"><a:tint val="37000"/><a:satMod val="300000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:tint val="15000"/><a:satMod val="350000"/></a:schemeClr></a:gs></a:gsLst><a:lin ang="16200000" scaled="1"/></a:gradFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:shade val="51000"/><a:satMod val="130000"/></a:schemeClr></a:gs><a:gs pos="80000"><a:schemeClr val="phClr"><a:shade val="93000"/><a:satMod val="130000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="94000"/><a:satMod val="135000"/></a:schemeClr></a:gs></a:gsLst><a:lin ang="16200000" scaled="0"/></a:gradFill>
            </a:fillStyleLst>
            <a:lnStyleLst>
                <a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"><a:shade val="95000"/><a:satMod val="105000"/></a:schemeClr></a:solidFill><a:prstDash val="solid"/></a:ln>
                <a:ln w="25400" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
                <a:ln w="38100" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
            </a:lnStyleLst>
            <a:effectStyleLst>
                <a:effectStyle>
                    <a:effectLst>
                        <a:outerShdw blurRad="40000" dist="20000" dir="5400000" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="38000"/></a:srgbClr></a:outerShdw>
                    </a:effectLst>
                </a:effectStyle>
                <a:effectStyle>
                    <a:effectLst>
                        <a:outerShdw blurRad="40000" dist="23000" dir="5400000" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="35000"/></a:srgbClr></a:outerShdw>
                    </a:effectLst>
                </a:effectStyle>
                <a:effectStyle>
                    <a:effectLst>
                        <a:outerShdw blurRad="40000" dist="23000" dir="5400000" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="35000"/></a:srgbClr></a:outerShdw>
                    </a:effectLst>
                    <a:scene3d>
                        <a:camera prst="orthographicFront">
                            <a:rot lat="0" lon="0" rev="0"/>
                        </a:camera>
                        <a:lightRig rig="threePt" dir="t">
                            <a:rot lat="0" lon="0" rev="1200000"/>
                        </a:lightRig>
                    </a:scene3d>
                    <a:sp3d>
                        <a:bevelT w="63500" h="25400"/>
                    </a:sp3d>
                </a:effectStyle>
            </a:effectStyleLst>
            <a:bgFillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="40000"/><a:satMod val="350000"/></a:schemeClr></a:gs><a:gs pos="40000"><a:schemeClr val="phClr"><a:tint val="45000"/><a:shade val="99000"/><a:satMod val="350000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="20000"/><a:satMod val="255000"/></a:schemeClr></a:gs></a:gsLst><a:path path="circle"><a:fillToRect l="50000" t="-80000" r="50000" b="180000"/></a:path></a:gradFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="80000"/><a:satMod val="300000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="30000"/><a:satMod val="200000"/></a:schemeClr></a:gs></a:gsLst><a:path path="circle"><a:fillToRect l="50000" t="50000" r="50000" b="50000"/></a:path></a:gradFill>
            </a:bgFillStyleLst>
        </a:fmtScheme>
    </a:themeElements>
</a:theme>"#, 
            secondary_color, primary_color, accent_color, primary_color, heading_font, body_font
        );
        
        self.add_file_to_zip(zip, "ppt/theme/theme1.xml", &content)?;
        Ok(())
    }
    
    fn add_slide_master(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>) -> Result<()> {
        let content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
    <p:cSld>
        <p:bg>
            <p:bgRef idx="1001">
                <a:schemeClr val="bg1"/>
            </p:bgRef>
        </p:bg>
        <p:spTree>
            <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
            </p:nvGrpSpPr>
            <p:grpSpPr>
                <a:xfrm>
                    <a:off x="0" y="0"/>
                    <a:ext cx="0" cy="0"/>
                    <a:chOff x="0" y="0"/>
                    <a:chExt cx="0" cy="0"/>
                </a:xfrm>
            </p:grpSpPr>
        </p:spTree>
    </p:cSld>
    <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
    <p:sldLayoutIdLst>
        <p:sldLayoutId id="2147483649" r:id="rId1"/>
    </p:sldLayoutIdLst>
</p:sldMaster>"#;
        
        self.add_file_to_zip(zip, "ppt/slideMasters/slideMaster1.xml", content)?;
        
        // Add slide master rels
        let rels_content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"#;
        
        self.add_file_to_zip(zip, "ppt/slideMasters/_rels/slideMaster1.xml.rels", rels_content)?;
        Ok(())
    }
    
    fn add_slide_layouts(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>) -> Result<()> {
        let content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="title" preserve="1">
    <p:cSld name="Title Slide">
        <p:spTree>
            <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
            </p:nvGrpSpPr>
            <p:grpSpPr>
                <a:xfrm>
                    <a:off x="0" y="0"/>
                    <a:ext cx="0" cy="0"/>
                    <a:chOff x="0" y="0"/>
                    <a:chExt cx="0" cy="0"/>
                </a:xfrm>
            </p:grpSpPr>
        </p:spTree>
    </p:cSld>
    <p:clrMapOvr>
        <a:masterClrMapping/>
    </p:clrMapOvr>
</p:sldLayout>"#;
        
        self.add_file_to_zip(zip, "ppt/slideLayouts/slideLayout1.xml", content)?;
        
        // Add slide layout rels
        let rels_content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"#;
        
        self.add_file_to_zip(zip, "ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels_content)?;
        Ok(())
    }
    
    fn add_slides(&self, zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>, contents: &[GeneratedContent]) -> Result<()> {
        let mut slide_number = 1;
        
        for content in contents {
            match content.content_type {
                crate::content::ContentType::Slides => {
                    self.add_slides_from_content(zip, content, &mut slide_number)?;
                }
                _ => {
                    // For non-slide content, create a single slide
                    self.add_single_content_slide(zip, content, slide_number)?;
                    slide_number += 1;
                }
            }
        }
        
        Ok(())
    }
    
    fn add_slides_from_content(
        &self,
        zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>,
        content: &GeneratedContent,
        slide_number: &mut usize
    ) -> Result<()> {
        let slides: Vec<&str> = content.content.split("---SLIDE---").collect();
        
        for slide_content in slides.iter() {
            if slide_content.trim().is_empty() {
                continue;
            }
            
            self.add_slide(zip, slide_content.trim(), &content.title, *slide_number)?;
            *slide_number += 1;
        }
        
        Ok(())
    }
    
    fn add_single_content_slide(
        &self,
        zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>,
        content: &GeneratedContent,
        slide_number: usize
    ) -> Result<()> {
        let slide_content = format!("{}\n\n{}", 
            self.format_content_type(&content.content_type),
            content.content
        );
        
        self.add_slide(zip, &slide_content, &content.title, slide_number)?;
        Ok(())
    }
    
    fn add_slide(
        &self,
        zip: &mut ZipWriter<Cursor<&mut Vec<u8>>>,
        slide_content: &str,
        title: &str,
        slide_number: usize
    ) -> Result<()> {
        // Extract title and content
        let lines: Vec<&str> = slide_content.lines().collect();
        let slide_title = if lines.len() > 0 && lines[0].starts_with('#') {
            lines[0].trim_start_matches('#').trim()
        } else {
            title
        };
        
        let body_content = if lines.len() > 0 && lines[0].starts_with('#') {
            lines[1..].join("\n")
        } else {
            slide_content.to_string()
        };
        
        let escaped_title = self.escape_xml(slide_title);
        let escaped_content = self.escape_xml(&body_content);
        
        let content = format!(r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
    <p:cSld>
        <p:spTree>
            <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
            </p:nvGrpSpPr>
            <p:grpSpPr>
                <a:xfrm>
                    <a:off x="0" y="0"/>
                    <a:ext cx="0" cy="0"/>
                    <a:chOff x="0" y="0"/>
                    <a:chExt cx="0" cy="0"/>
                </a:xfrm>
            </p:grpSpPr>
            <p:sp>
                <p:nvSpPr>
                    <p:cNvPr id="2" name="Title 1"/>
                    <p:cNvSpPr>
                        <a:spLocks noGrp="1"/>
                    </p:cNvSpPr>
                    <p:nvPr>
                        <p:ph type="ctrTitle"/>
                    </p:nvPr>
                </p:nvSpPr>
                <p:spPr/>
                <p:txBody>
                    <a:bodyPr/>
                    <a:lstStyle/>
                    <a:p>
                        <a:r>
                            <a:rPr lang="en-US" dirty="0" smtClean="0"/>
                            <a:t>{}</a:t>
                        </a:r>
                        <a:endParaRPr lang="en-US" dirty="0"/>
                    </a:p>
                </p:txBody>
            </p:sp>
            <p:sp>
                <p:nvSpPr>
                    <p:cNvPr id="3" name="Content Placeholder 2"/>
                    <p:cNvSpPr>
                        <a:spLocks noGrp="1"/>
                    </p:cNvSpPr>
                    <p:nvPr>
                        <p:ph idx="1"/>
                    </p:nvPr>
                </p:nvSpPr>
                <p:spPr/>
                <p:txBody>
                    <a:bodyPr/>
                    <a:lstStyle/>
                    <a:p>
                        <a:r>
                            <a:rPr lang="en-US" dirty="0" smtClean="0"/>
                            <a:t>{}</a:t>
                        </a:r>
                        <a:endParaRPr lang="en-US" dirty="0"/>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
    <p:clrMapOvr>
        <a:masterClrMapping/>
    </p:clrMapOvr>
</p:sld>"#, escaped_title, escaped_content);
        
        let filename = format!("ppt/slides/slide{}.xml", slide_number);
        self.add_file_to_zip(zip, &filename, &content)?;
        
        // Add slide rels
        let rels_content = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"#;
        
        let rels_filename = format!("ppt/slides/_rels/slide{}.xml.rels", slide_number);
        self.add_file_to_zip(zip, &rels_filename, rels_content)?;
        
        Ok(())
    }
    
    fn count_total_slides(&self, contents: &[GeneratedContent]) -> usize {
        let mut total = 0;
        
        for content in contents {
            match content.content_type {
                crate::content::ContentType::Slides => {
                    let slides: Vec<&str> = content.content.split("---SLIDE---").collect();
                    total += slides.iter().filter(|s| !s.trim().is_empty()).count();
                }
                _ => {
                    total += 1; // One slide per non-slide content
                }
            }
        }
        
        total
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
impl FormatConverter for PowerPointConverter {
    fn supported_format(&self) -> ExportFormat {
        ExportFormat::PowerPoint
    }

    async fn convert(&self, contents: &[GeneratedContent], options: &ExportOptions) -> Result<ExportResult> {
        // Generate the PowerPoint content
        let pptx_bytes = self.content_to_pptx(contents, options)
            .context("Failed to create PowerPoint document")?;

        // Ensure the output directory exists
        if let Some(parent) = options.output_path.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create output directory")?;
        }

        // Write the PowerPoint file
        fs::write(&options.output_path, &pptx_bytes)
            .context("Failed to write PowerPoint file")?;

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
            content_type: ContentType::Slides,
            title: "Test Lesson".to_string(),
            content: "---SLIDE---\n# Introduction\nThis is slide 1\n---SLIDE---\n# Main Content\nThis is slide 2".to_string(),
            metadata: ContentMetadata {
                word_count: 15,
                estimated_duration: "30 minutes".to_string(),
                difficulty_level: "Intermediate".to_string(),
            },
        }
    }

    #[tokio::test]
    async fn test_powerpoint_conversion() {
        let converter = PowerPointConverter::new();
        let content = create_test_content();
        
        let result = converter.content_to_pptx(&[content], &ExportOptions {
            format: ExportFormat::PowerPoint,
            output_path: std::path::PathBuf::from("/tmp/test.pptx"),
            template_name: None,
            include_metadata: true,
        });
        
        assert!(result.is_ok());
        let pptx_bytes = result.unwrap();
        assert!(!pptx_bytes.is_empty());
        
        // Check that it starts with ZIP header (PK)
        let zip_header = &pptx_bytes[0..2];
        assert_eq!(zip_header, b"PK");
    }

    #[tokio::test]
    async fn test_full_powerpoint_export() {
        let converter = PowerPointConverter::new();
        let contents = vec![create_test_content()];
        
        let temp_dir = std::env::temp_dir();
        let output_path = temp_dir.join("test_export.pptx");
        
        let options = ExportOptions {
            format: ExportFormat::PowerPoint,
            output_path: output_path.clone(),
            template_name: None,
            include_metadata: true,
        };

        let result = converter.convert(&contents, &options).await;
        assert!(result.is_ok());
        
        let export_result = result.unwrap();
        assert!(export_result.success);
        assert!(export_result.file_size.is_some());
        assert!(export_result.file_size.unwrap() > 0);
        
        // Verify file exists and has ZIP header (PowerPoint files are ZIP archives)
        assert!(output_path.exists());
        let file_content = std::fs::read(&output_path).unwrap();
        assert!(file_content.starts_with(b"PK"));
        
        // Cleanup
        if output_path.exists() {
            let _ = std::fs::remove_file(output_path);
        }
    }

    #[test]
    fn test_count_slides() {
        let converter = PowerPointConverter::new();
        let content = create_test_content();
        let count = converter.count_total_slides(&[content]);
        assert_eq!(count, 2); // Two slides from the test content
    }

    #[test]
    fn test_xml_escaping() {
        let converter = PowerPointConverter::new();
        let test_text = "Test & <example> with \"quotes\" and 'apostrophes'";
        let escaped = converter.escape_xml(test_text);
        assert_eq!(escaped, "Test &amp; &lt;example&gt; with &quot;quotes&quot; and &apos;apostrophes&apos;");
    }
}