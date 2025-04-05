"""Structure validator to ensure content has the required structure."""

import re
from typing import Any, Dict, List, Optional

from curriculum_curator.validation.validators.base import BaseValidator


class StructureValidator(BaseValidator):
    """Validator that ensures content follows a required structure.
    
    Checks if the content has the required sections and meets minimum structural
    requirements. Particularly useful for educational content that needs specific
    sections like "Objectives", "Assessment", etc.
    
    Config options:
        min_sections: Minimum number of sections required
        required_sections: List of required section names
    """
    
    def __init__(self, config: Any):
        """Initialize the structure validator.
        
        Args:
            config: Configuration for the validator
        """
        super().__init__(config)
        self.min_sections = getattr(config, "min_sections", 0)
        self.required_sections = getattr(config, "required_sections", [])
    
    async def validate(self, content: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check if content has the required structure.
        
        Args:
            content: The content to validate
            context: Optional context with additional requirements
            
        Returns:
            dict: Validation result with structure information
        """
        sections = self._extract_sections(content)
        
        issues = []
        
        # Check minimum number of sections
        if len(sections) < self.min_sections:
            issues.append({
                "issue": "min_sections",
                "message": f"Content has {len(sections)} sections, but {self.min_sections} are required",
                "sections_found": len(sections),
                "min_sections": self.min_sections
            })
        
        # Check required sections
        missing_sections = []
        for required in self.required_sections:
            if not any(self._section_matches(section, required) for section in sections):
                missing_sections.append(required)
        
        if missing_sections:
            issues.append({
                "issue": "missing_sections",
                "message": f"Missing required sections: {', '.join(missing_sections)}",
                "missing_sections": missing_sections
            })
        
        if issues:
            return {
                "valid": False,
                "reason": "Structure validation failed",
                "issues": issues,
                "sections_found": sections
            }
        
        return {
            "valid": True,
            "sections_found": sections
        }
    
    def _extract_sections(self, content: str) -> List[str]:
        """Extract section headings from content.
        
        Args:
            content: The content to extract sections from
            
        Returns:
            list: List of section headings
        """
        section_pattern = r'^(#{1,6})\s+(.+?)$'
        sections = []
        
        for line in content.split('\n'):
            match = re.match(section_pattern, line)
            if match:
                sections.append(match.group(2).strip())
        
        return sections
    
    def _section_matches(self, section: str, required: str) -> bool:
        """Check if a section matches a required section name.
        
        Performs case-insensitive comparison and allows for some flexibility
        in matching (e.g., "Learning Objectives" matches "Objectives").
        
        Args:
            section: The section name found in the content
            required: The required section name
            
        Returns:
            bool: True if the section matches the required name
        """
        section_lower = section.lower()
        required_lower = required.lower()
        
        # Exact match
        if section_lower == required_lower:
            return True
        
        # Contains match
        if required_lower in section_lower:
            return True
        
        # TODO: Implement more sophisticated matching if needed
        
        return False
    
    def get_remediation_hints(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get hints for remediation if structure validation fails.
        
        Args:
            validation_result: The validation result
            
        Returns:
            dict: Remediation hints
        """
        if validation_result.get("valid", True):
            return {"can_remediate": False, "hints": []}
        
        hints = []
        issues = validation_result.get("issues", [])
        
        for issue in issues:
            if issue.get("issue") == "min_sections":
                hints.append(f"Add more sections (at least {issue['min_sections']} needed)")
            
            if issue.get("issue") == "missing_sections":
                missing = issue.get("missing_sections", [])
                for section in missing:
                    hints.append(f"Add a '{section}' section")
        
        return {
            "can_remediate": True,
            "hints": hints
        }