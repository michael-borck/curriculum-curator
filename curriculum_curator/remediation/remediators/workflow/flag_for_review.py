"""Flag for review remediator for marking content for human review."""

from typing import Any, Dict, List, Optional

from curriculum_curator.remediation.remediators.base import BaseRemediator


class FlagForReview(BaseRemediator):
    """Remediator that flags content for human review.
    
    Marks sections with issues that require human intervention.
    
    Config options:
        severity_threshold: Minimum severity level to flag for review
        always_flag_validators: List of validators whose issues always require review
    """
    
    def __init__(self, config: Any):
        """Initialize the flag for review remediator.
        
        Args:
            config: Configuration for the remediator
        """
        super().__init__(config)
        self.severity_threshold = getattr(config, "severity_threshold", "medium")
        self.always_flag_validators = getattr(config, "always_flag_validators", [
            "FactualityValidator", "SafetyValidator"
        ])
    
    async def remediate(
        self, 
        content: str, 
        issues: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Flag content for human review based on validation issues.
        
        Args:
            content: The content to remediate
            issues: List of validation issues to address
            context: Optional context with additional information
            
        Returns:
            dict: Remediation result
        """
        # This remediator doesn't actually change the content,
        # it just flags it for review
        
        flags = []
        
        # Identify issues that need review
        for issue in issues:
            validator = issue.get("validator", "unknown")
            severity = issue.get("severity", "medium")
            message = issue.get("message", "Unspecified issue")
            
            # Determine if this issue requires human review
            requires_review = (
                validator in self.always_flag_validators or
                self._severity_above_threshold(severity)
            )
            
            if requires_review:
                flags.append({
                    "type": "human_review_flag",
                    "validator": validator,
                    "severity": severity,
                    "message": message,
                    "details": issue
                })
        
        return {
            "remediated_content": content,  # Unchanged
            "remediation_actions": flags,
            "success": True,  # Always succeeds in flagging
            "flags_for_review": len(flags)
        }
    
    def _severity_above_threshold(self, severity: str) -> bool:
        """Check if a severity level is at or above the threshold.
        
        Args:
            severity: The severity level to check
            
        Returns:
            bool: True if the severity is at or above the threshold
        """
        severity_levels = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        
        issue_level = severity_levels.get(severity.lower(), 2)  # Default to medium
        threshold_level = severity_levels.get(self.severity_threshold.lower(), 2)
        
        return issue_level >= threshold_level
    
    def can_remediate_issues(self, issues: List[Dict[str, Any]]) -> bool:
        """Check if this remediator can handle the given issues.
        
        Args:
            issues: List of validation issues
            
        Returns:
            bool: True if this remediator can handle the issues
        """
        # This remediator is always able to flag issues, as long as there are any
        return len(issues) > 0