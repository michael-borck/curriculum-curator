"""Rephrasing prompter for LLM-assisted content rewriting."""

import re
from typing import Any, Dict, List, Optional

from curriculum_curator.remediation.remediators.base import BaseRemediator


class RephrasingPrompter(BaseRemediator):
    """Remediator that uses an LLM to rewrite problematic content.
    
    Takes content with issues and passes it to an LLM with specific
    instructions for rewriting or improving the section.
    
    Config options:
        model_alias: LLM model to use for rewriting
        max_tokens: Maximum tokens for LLM response
        temperature: Temperature for LLM generation
        prompt_templates: Templates for different issue types
    """
    
    def __init__(self, config: Any):
        """Initialize the rephrasing prompter.
        
        Args:
            config: Configuration for the remediator
        """
        super().__init__(config)
        self.model_alias = getattr(config, "model_alias", None)  # Uses default if None
        self.max_tokens = getattr(config, "max_tokens", 1000)
        self.temperature = getattr(config, "temperature", 0.7)
        self.prompt_templates = getattr(config, "prompt_templates", {
            "default": "Rewrite the following text to improve its quality: {text}",
            "readability": "Rewrite the following text to improve readability and make it easier to understand: {text}",
            "similarity": "Rewrite the following text to make it more unique and distinct: {text}",
            "tone": "Rewrite the following text to match a {tone} tone: {text}",
        })
    
    async def remediate(
        self, 
        content: str, 
        issues: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Remediate content by requesting LLM rewrites for problematic sections.
        
        Args:
            content: The content to remediate
            issues: List of validation issues to address
            context: Optional context with additional information
            
        Returns:
            dict: Remediation result
        """
        # Placeholder implementation - real version would integrate with LLMManager
        actions = []
        remediated_content = content
        
        # Group issues by validator
        issue_groups = {}
        for issue in issues:
            validator = issue.get("validator", "unknown")
            if validator not in issue_groups:
                issue_groups[validator] = []
            issue_groups[validator].append(issue)
        
        # Simulate rewriting by issue type
        for validator, validator_issues in issue_groups.items():
            # Determine prompt template
            template_key = "default"
            if "readability" in validator.lower():
                template_key = "readability"
            elif "similarity" in validator.lower():
                template_key = "similarity"
            elif "tone" in validator.lower():
                template_key = "tone"
            
            prompt_template = self.prompt_templates.get(template_key, self.prompt_templates["default"])
            
            # Simulate LLM call (in real implementation, would call LLMManager.generate)
            actions.append({
                "type": "llm_rewrite",
                "validator": validator,
                "issues_count": len(validator_issues),
                "prompt_template": template_key,
                "model_alias": self.model_alias,
                "section": "full_document",  # Would be more specific in real implementation
            })
        
        return {
            "remediated_content": remediated_content,
            "remediation_actions": actions,
            "success": len(actions) > 0,
            "sections_rewritten": len(actions)
        }
    
    def can_remediate_issues(self, issues: List[Dict[str, Any]]) -> bool:
        """Check if this remediator can handle the given issues.
        
        Args:
            issues: List of validation issues
            
        Returns:
            bool: True if this remediator can handle the issues
        """
        # This remediator can handle most content quality issues
        if not issues:
            return False
            
        # Prefer not to handle purely structural/formatting issues
        issue_types = set()
        for issue in issues:
            validator = issue.get("validator", "").lower()
            issue_types.add(validator)
            
        # If only structure validator issues, don't use this remediator
        if len(issue_types) == 1 and "structure" in next(iter(issue_types)).lower():
            return False
            
        return True