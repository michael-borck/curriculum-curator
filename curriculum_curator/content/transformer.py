import re
import json
import markdown
from bs4 import BeautifulSoup
import structlog

logger = structlog.get_logger()


class ContentTransformer:
    """Transforms raw LLM outputs into structured formats."""
    
    def __init__(self):
        """Initialize the content transformer."""
        logger.info("content_transformer_initialized")
    
    def transform(self, raw_content, output_format, transformation_rules=None):
        """Transform raw LLM output into the desired format.
        
        Args:
            raw_content (str): The raw text from the LLM
            output_format (str): Desired output format ('raw', 'list', 'json', 'html')
            transformation_rules (dict, optional): Additional transformation rules
            
        Returns:
            Various: Transformed content in the requested format
        """
        if output_format == "raw":
            return raw_content
        
        if output_format == "list":
            return self._extract_list_items(raw_content)
        
        if output_format == "json":
            return self._extract_json(raw_content)
        
        if output_format == "html":
            return self._markdown_to_html(raw_content)
        
        # Default to returning the raw content
        logger.warning("unknown_output_format", format=output_format)
        return raw_content
    
    def _extract_list_items(self, content):
        """Extract list items from markdown content.
        
        Args:
            content (str): Markdown content with list items
            
        Returns:
            list: Extracted list items
        """
        items = []
        for line in content.split('\n'):
            # Match Markdown list items (both - and * style)
            match = re.match(r'^\s*[-*]\s+(.+)$', line)
            if match:
                items.append(match.group(1).strip())
            
            # Match numbered list items
            match = re.match(r'^\s*\d+\.\s+(.+)$', line)
            if match:
                items.append(match.group(1).strip())
                
        logger.debug("extracted_list_items", count=len(items))
        return items
    
    def _extract_json(self, content):
        """Extract JSON from the content.
        
        Args:
            content (str): Content that may contain JSON
            
        Returns:
            dict or list: Parsed JSON object or empty dict if parsing fails
        """
        # Find content between triple backticks and json
        match = re.search(r'```(?:json)?\n([\s\S]*?)\n```', content)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.warning("json_decode_error_in_code_block")
        
        # Try parsing the entire content as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("json_decode_error_in_full_content")
        
        # Return empty dict if no valid JSON found
        return {}
    
    def _markdown_to_html(self, content):
        """Convert markdown to HTML.
        
        Args:
            content (str): Markdown content
            
        Returns:
            str: HTML content
        """
        html = markdown.markdown(content)
        logger.debug("converted_markdown_to_html", 
                    markdown_length=len(content),
                    html_length=len(html))
        return html
    
    def extract_sections(self, content, section_markers=None):
        """Extract sections from content based on markdown headings.
        
        Args:
            content (str): Markdown content with sections
            section_markers (list, optional): List of section names to extract
            
        Returns:
            dict: Dictionary of section name to section content
        """
        if section_markers is None:
            # Default to extracting sections by headings
            sections = {}
            current_section = None
            current_content = []
            
            for line in content.split('\n'):
                heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
                if heading_match:
                    # Save previous section if exists
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    
                    # Start new section
                    current_section = heading_match.group(2).strip()
                    current_content = []
                else:
                    if current_section:
                        current_content.append(line)
                    
            # Save the last section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
                
            logger.debug("extracted_sections_by_headings", count=len(sections))
            return sections
        else:
            # Use custom section markers
            sections = {}
            for marker in section_markers:
                pattern = f"### {re.escape(marker)}\\s*\\n([\\s\\S]*?)(?=### [^#]|$)"
                match = re.search(pattern, content)
                if match:
                    sections[marker] = match.group(1).strip()
            
            logger.debug("extracted_sections_by_markers", 
                        markers=section_markers,
                        found=list(sections.keys()))
            return sections
    
    def extract_code_blocks(self, content, language=None):
        """Extract code blocks from markdown content.
        
        Args:
            content (str): Markdown content with code blocks
            language (str, optional): Filter blocks by programming language
            
        Returns:
            list: List of extracted code blocks
        """
        if language:
            pattern = f"```{language}\n(.*?)```"
        else:
            pattern = r"```(\w*)\n(.*?)```"
            
        # Find all code blocks with re.DOTALL to match across multiple lines
        matches = re.finditer(pattern, content, re.DOTALL)
        
        blocks = []
        for match in matches:
            if language:
                # If language specified, we matched directly to the code content
                blocks.append(match.group(1))
            else:
                # If no language filter, we need groups for both language and content
                lang = match.group(1)
                code = match.group(2)
                blocks.append({"language": lang, "code": code})
        
        logger.debug("extracted_code_blocks", count=len(blocks))
        return blocks