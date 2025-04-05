import structlog
from abc import ABC, abstractmethod

# Import validators as they are implemented
# from curriculum_curator.validation.validators.similarity import SimilarityValidator
# from curriculum_curator.validation.validators.structure import StructureValidator
# from curriculum_curator.validation.validators.readability import ReadabilityValidator

logger = structlog.get_logger()


class ValidationIssue:
    """Represents an issue found during validation."""
    
    def __init__(self, severity, message, location=None, suggestion=None):
        """Initialize a validation issue.
        
        Args:
            severity (str): Severity level ('error', 'warning', 'info')
            message (str): Description of the issue
            location (str, optional): Location of the issue in the content
            suggestion (str, optional): Suggested fix for the issue
        """
        self.severity = severity
        self.message = message
        self.location = location
        self.suggestion = suggestion
    
    def __str__(self):
        """String representation of the issue."""
        return f"{self.severity.upper()}: {self.message}"
    
    def to_dict(self):
        """Convert the issue to a dictionary."""
        return {
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion
        }


class Validator(ABC):
    """Base class for content validators."""
    
    def __init__(self, config):
        """Initialize a validator.
        
        Args:
            config (dict): Validator configuration
        """
        self.config = config
    
    @abstractmethod
    async def validate(self, content, context=None):
        """Validate content and return a list of validation issues.
        
        Args:
            content (str or dict): Content to validate
            context (dict, optional): Additional context for validation
            
        Returns:
            list: List of ValidationIssue objects
        """
        pass


class ValidationManager:
    """Manages and coordinates validation of content."""
    
    def __init__(self, config):
        """Initialize the validation manager.
        
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
            
        self.validators = {}
        self._initialize_validators()
        
        logger.info("validation_manager_initialized", 
                   validators=list(self.validators.keys()))
    
    def _initialize_validators(self):
        """Initialize validators from configuration."""
        from curriculum_curator.validation.validators import VALIDATOR_REGISTRY, get_validator
        
        # Create empty validators dictionary
        self.validators = {}
        
        if self.config.validation:
            # Initialize validators from registry based on configuration
            
            # Quality validators
            if hasattr(self.config.validation, "similarity") and self.config.validation.similarity:
                self.validators["similarity"] = get_validator("similarity", self.config.validation.similarity)
            
            if hasattr(self.config.validation, "structure") and self.config.validation.structure:
                # Structure validator can have multiple configurations for different content types
                if isinstance(self.config.validation.structure, dict):
                    for content_type, config in self.config.validation.structure.items():
                        validator_name = f"structure_{content_type}"
                        self.validators[validator_name] = get_validator("structure", config)
                else:
                    self.validators["structure"] = get_validator("structure", self.config.validation.structure)
            
            if hasattr(self.config.validation, "readability") and self.config.validation.readability:
                self.validators["readability"] = get_validator("readability", self.config.validation.readability)
        
        logger.info(
            "validators_initialized", 
            validators=list(self.validators.keys())
        )
    
    async def validate(self, content, validator_names=None, context=None):
        """Run specified validators on content.
        
        Args:
            content (str or dict): Content to validate
            validator_names (list, optional): Names of validators to run
            context (dict, optional): Additional context for validation
            
        Returns:
            list: List of validation issues
        """
        all_issues = []
        
        # Determine which validators to run
        if validator_names is None:
            validators_to_run = list(self.validators.values())
        else:
            validators_to_run = [
                self.validators[name] for name in validator_names 
                if name in self.validators
            ]
        
        # Run each validator
        for validator in validators_to_run:
            validator_name = validator.__class__.__name__
            logger.info(
                "running_validator",
                validator=validator_name,
                content_type=type(content).__name__,
                content_length=len(content) if isinstance(content, str) else "N/A"
            )
            
            try:
                result = await validator.validate(content, context)
                
                # If validation failed, add the issues to our collection
                if not result.get("valid", True):
                    # Convert the validation result to issues
                    issues = result.get("issues", [])
                    
                    # If there are no specific issues but validation failed,
                    # create a generic issue
                    if not issues and "reason" in result:
                        issues = [{
                            "validator": validator_name,
                            "message": result["reason"],
                            "details": result
                        }]
                    
                    # Add validator name to each issue
                    for issue in issues:
                        if "validator" not in issue:
                            issue["validator"] = validator_name
                    
                    all_issues.extend(issues)
                
                logger.info(
                    "validator_completed",
                    validator=validator_name,
                    valid=result.get("valid", True),
                    issues_found=len(issues) if not result.get("valid", True) else 0
                )
            except Exception as e:
                logger.exception(
                    "validator_error",
                    validator=validator_name,
                    error=str(e)
                )
                all_issues.append({
                    "validator": validator_name,
                    "message": f"Validator error: {str(e)}",
                    "error": str(e)
                })
        
        return all_issues
        #         )
        #     except Exception as e:
        #         logger.exception(
        #             "validator_failed",
        #             validator=validator_name,
        #             error=str(e)
        #         )
        #         
        #         all_issues.append(ValidationIssue(
        #             "error",
        #             f"Validation failed: {str(e)}",
        #             None,
        #             None
        #         ))
        # 
        # return all_issues