"""Manager for content remediation."""

import structlog
from typing import Any, Dict, List, Optional, Type

from curriculum_curator.remediation.remediators.base import BaseRemediator

logger = structlog.get_logger()


class RemediationManager:
    """Manager for content remediation.
    
    Provides a centralized interface for remediating content issues
    using different remediators based on the type of issue.
    """
    
    def __init__(self, config):
        """Initialize the remediation manager.
        
        Args:
            config: Configuration (either dict or AppConfig)
        """
        from curriculum_curator.config.models import AppConfig
        
        # Convert dict to AppConfig if needed
        if not isinstance(config, AppConfig):
            from curriculum_curator.config.models import AppConfig
            self.config = AppConfig.model_validate(config)
        else:
            self.config = config
            
        self.remediators = {}
        self._initialize_remediators()
        
        logger.info("remediation_manager_initialized", 
                   remediators=list(self.remediators.keys()))
    
    def _initialize_remediators(self):
        """Initialize remediators from configuration."""
        from curriculum_curator.remediation.remediators import REMEDIATOR_REGISTRY, get_remediator
        
        # Create empty remediators dictionary
        self.remediators = {}
        
        if self.config.remediation:
            # Initialize common remediators that should always be available
            remediator_configs = {
                "format_corrector": getattr(self.config.remediation, "format_corrector", {}),
                "sentence_splitter": getattr(self.config.remediation, "sentence_splitter", {}),
                "flag_for_review": getattr(self.config.remediation, "flag_for_review", {}),
            }
            
            # Initialize remediators from registry based on configuration
            for remediator_name, config in remediator_configs.items():
                if config is not None:
                    try:
                        self.remediators[remediator_name] = get_remediator(remediator_name, config)
                    except ValueError as e:
                        logger.warning("remediator_init_failed", 
                                      remediator=remediator_name, 
                                      error=str(e))
        
        logger.info(
            "remediators_initialized", 
            remediators=list(self.remediators.keys())
        )
    
    async def remediate(
        self, 
        content: str, 
        issues: List[Dict[str, Any]], 
        remediator_names: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Remediate content issues using appropriate remediators.
        
        Args:
            content: The content to remediate
            issues: List of validation issues to address
            remediator_names: Optional list of specific remediators to use
            context: Optional context with additional information
            
        Returns:
            dict: Remediation result with modified content and actions taken
        """
        if not issues:
            return {
                "remediated_content": content,
                "remediation_actions": [],
                "success": True,
                "message": "No issues to remediate"
            }
        
        # Determine which remediators to run
        if remediator_names:
            remediators_to_run = [
                self.remediators[name] for name in remediator_names 
                if name in self.remediators
            ]
        else:
            # Auto-select remediators based on issues
            remediators_to_run = []
            for name, remediator in self.remediators.items():
                if remediator.can_remediate_issues(issues):
                    remediators_to_run.append(remediator)
        
        if not remediators_to_run:
            return {
                "remediated_content": content,
                "remediation_actions": [],
                "success": False,
                "message": "No suitable remediators found for the given issues"
            }
        
        # Run remediators in sequence
        remediated_content = content
        all_actions = []
        success = True
        
        for remediator in remediators_to_run:
            try:
                logger.info(
                    "running_remediator",
                    remediator=remediator.__class__.__name__,
                    issues_count=len(issues)
                )
                
                result = await remediator.remediate(remediated_content, issues, context)
                
                # If this remediator modified the content, update it for the next remediator
                if "remediated_content" in result:
                    remediated_content = result["remediated_content"]
                
                # Collect actions from this remediator
                if "remediation_actions" in result:
                    actions = result["remediation_actions"]
                    if actions:
                        for action in actions:
                            if "remediator" not in action:
                                action["remediator"] = remediator.__class__.__name__
                        
                        all_actions.extend(actions)
                
                # Record success status
                if "success" in result and not result["success"]:
                    success = False
                    
                logger.info(
                    "remediator_completed",
                    remediator=remediator.__class__.__name__,
                    actions_count=len(result.get("remediation_actions", [])),
                    success=result.get("success", True)
                )
                
            except Exception as e:
                logger.exception(
                    "remediator_failed",
                    remediator=remediator.__class__.__name__,
                    error=str(e)
                )
                success = False
                all_actions.append({
                    "remediator": remediator.__class__.__name__,
                    "type": "error",
                    "message": f"Remediator error: {str(e)}",
                    "error": str(e)
                })
        
        return {
            "remediated_content": remediated_content,
            "remediation_actions": all_actions,
            "success": success,
            "remediators_run": [r.__class__.__name__ for r in remediators_to_run],
            "message": "Remediation completed" if success else "Remediation completed with issues"
        }
    
    def get_available_remediators(self) -> List[str]:
        """Get list of available remediator names.
        
        Returns:
            list: List of remediator names
        """
        return list(self.remediators.keys())