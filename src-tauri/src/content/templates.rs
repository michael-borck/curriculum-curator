use serde::{Deserialize, Serialize};
use tera::{Tera, Context};
use anyhow::Result;
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentTemplate {
    pub name: String,
    pub template_content: String,
    pub variables: Vec<String>,
    pub content_type: crate::content::ContentType,
}

pub struct TemplateManager {
    templates: HashMap<String, ContentTemplate>,
    tera: Tera,
}

impl TemplateManager {
    pub fn new() -> Result<Self> {
        let mut tera = Tera::new("templates/**/*")?;
        tera.autoescape_on(vec![]);
        
        Ok(Self {
            templates: HashMap::new(),
            tera,
        })
    }

    pub fn add_template(&mut self, template: ContentTemplate) {
        self.templates.insert(template.name.clone(), template);
    }

    pub fn render_template(&mut self, name: &str, context: &Context) -> Result<String> {
        let template = self.templates.get(name)
            .ok_or_else(|| anyhow::anyhow!("Template '{}' not found", name))?;
        
        let rendered = self.tera.render_str(&template.template_content, context)?;
        Ok(rendered)
    }

    pub fn list_templates(&self) -> Vec<&ContentTemplate> {
        self.templates.values().collect()
    }
}