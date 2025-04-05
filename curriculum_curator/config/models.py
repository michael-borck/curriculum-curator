"""Pydantic models for configuration data."""

import os
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class TokenCostConfig(BaseModel):
    """Cost per 1k tokens configuration."""

    input: float = Field(default=0.0, description="Cost per 1k input tokens")
    output: float = Field(default=0.0, description="Cost per 1k output tokens")


class LLMModelConfig(BaseModel):
    """Configuration for a specific LLM model."""

    cost_per_1k_tokens: Optional[TokenCostConfig] = None


class LLMProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    api_key: Optional[str] = Field(
        default=None, description="API key or environment variable reference"
    )
    default_model: str = Field(..., description="Default model for this provider")
    base_url: Optional[str] = Field(default=None, description="Base URL for API calls")
    cost_per_1k_tokens: TokenCostConfig = Field(
        default_factory=TokenCostConfig, description="Default token costs for this provider"
    )
    models: Dict[str, LLMModelConfig] = Field(
        default_factory=dict, description="Available models for this provider"
    )

    @field_validator("api_key")
    @classmethod
    def resolve_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Resolve API key from environment variables if needed."""
        if not v:
            return v
        if v.startswith("env(") and v.endswith(")"):
            env_var = v[4:-1]
            return os.getenv(env_var, "")
        return v


class LLMConfig(BaseModel):
    """LLM configuration."""

    default_provider: str = Field(..., description="Default LLM provider to use")
    aliases: Dict[str, str] = Field(
        default_factory=dict, description="Model aliases for easier reference"
    )
    providers: Dict[str, LLMProviderConfig] = Field(
        default_factory=dict, description="LLM provider configurations"
    )


class PromptConfig(BaseModel):
    """Prompt registry configuration."""

    base_path: str = Field(
        default="./prompts", description="Base path for prompt template files"
    )


class SystemConfig(BaseModel):
    """System configuration."""

    persistence_dir: str = Field(
        default=".curriculum_curator", description="Directory for persistent session data"
    )
    output_dir: str = Field(default="output", description="Directory for output files")
    log_level: str = Field(default="INFO", description="Logging level")


class ValidationSimilarityConfig(BaseModel):
    """Configuration for similarity validation."""

    threshold: float = Field(
        default=0.85,
        description="Similarity threshold above which content is considered duplicate",
        ge=0.0,
        le=1.0,
    )
    model: Optional[str] = Field(
        default=None, description="Embedding model for similarity calculation"
    )


class ValidationStructureConfig(BaseModel):
    """Configuration for structure validation."""

    min_sections: int = Field(
        default=0, description="Minimum number of sections required", ge=0
    )
    required_sections: List[str] = Field(
        default_factory=list, description="List of required section names"
    )


class ValidationReadabilityConfig(BaseModel):
    """Configuration for readability validation."""

    max_avg_sentence_length: int = Field(
        default=25, description="Maximum average sentence length", ge=0
    )
    min_flesch_reading_ease: float = Field(
        default=60.0,
        description="Minimum Flesch Reading Ease score",
        ge=0.0,
        le=100.0,
    )


class ValidationLanguageConfig(BaseModel):
    """Configuration for language validation."""
    
    expected_language: str = Field(default="en", description="Expected language code")
    allow_multilingual: bool = Field(default=False, description="Whether to allow mixed languages")
    confidence_threshold: float = Field(
        default=0.8, 
        description="Minimum confidence for language detection",
        ge=0.0,
        le=1.0
    )


class ValidationConfig(BaseModel):
    """Validation configuration."""

    similarity: Optional[ValidationSimilarityConfig] = None
    structure: Optional[Dict[str, ValidationStructureConfig]] = None
    readability: Optional[ValidationReadabilityConfig] = None
    language: Optional[ValidationLanguageConfig] = None


class FormatCorrectorConfig(BaseModel):
    """Format corrector remediator configuration."""
    
    heading_levels: int = Field(default=6, description="Number of heading levels to enforce")
    enforce_consistency: bool = Field(default=True, description="Whether to enforce consistent formatting")


class SentenceSplitterConfig(BaseModel):
    """Sentence splitter remediator configuration."""
    
    max_sentence_length: int = Field(default=25, description="Maximum allowed sentence length")
    split_points: List[str] = Field(
        default_factory=lambda: [
            r'\s+and\s+', r'\s+but\s+', r'\s+or\s+', r'\s+nor\s+', 
            r'\s+yet\s+', r'\s+so\s+', r'\s+for\s+', r';'
        ],
        description="Regular expression patterns for sentence splitting points"
    )


class TerminologyEnforcerConfig(BaseModel):
    """Terminology enforcer remediator configuration."""
    
    terminology_map: Dict[str, str] = Field(
        default_factory=dict, description="Mapping of incorrect terms to preferred terms"
    )
    case_sensitive: bool = Field(default=False, description="Whether to use case-sensitive matching")
    whole_word_only: bool = Field(default=True, description="Whether to match only whole words")


class RephrasingPrompterConfig(BaseModel):
    """Rephrasing prompter remediator configuration."""
    
    model_alias: Optional[str] = Field(default=None, description="LLM model to use for rewriting")
    max_tokens: int = Field(default=1000, description="Maximum tokens for LLM response")
    temperature: float = Field(default=0.7, description="Temperature for LLM generation")
    prompt_templates: Dict[str, str] = Field(
        default_factory=lambda: {
            "default": "Rewrite the following text to improve its quality: {text}",
            "readability": "Rewrite the following text to improve readability and make it easier to understand: {text}",
            "similarity": "Rewrite the following text to make it more unique and distinct: {text}",
            "tone": "Rewrite the following text to match a {tone} tone: {text}",
        },
        description="Templates for different issue types"
    )


class FlagForReviewConfig(BaseModel):
    """Flag for review remediator configuration."""
    
    severity_threshold: str = Field(default="medium", description="Minimum severity level to flag for review")
    always_flag_validators: List[str] = Field(
        default_factory=lambda: ["FactualityValidator", "SafetyValidator"],
        description="List of validators whose issues always require review"
    )


class TranslatorConfig(BaseModel):
    """Translator remediator configuration."""
    
    target_language: str = Field(default="en", description="Target language code")
    source_language: str = Field(default="auto", description="Source language code, or 'auto' for auto-detection")
    use_llm: bool = Field(default=True, description="Whether to use LLM for translation")
    model_alias: Optional[str] = Field(default=None, description="LLM model to use if use_llm is True")
    preserve_formatting: bool = Field(default=True, description="Whether to preserve Markdown formatting")


class RemediationConfig(BaseModel):
    """Remediation configuration."""

    # AutoFix remediators
    format_corrector: Optional[FormatCorrectorConfig] = None
    sentence_splitter: Optional[SentenceSplitterConfig] = None
    terminology_enforcer: Optional[TerminologyEnforcerConfig] = None
    
    # Rewrite remediators
    rephrasing_prompter: Optional[RephrasingPrompterConfig] = None
    
    # Workflow remediators
    flag_for_review: Optional[FlagForReviewConfig] = None
    
    # Language remediators
    translator: Optional[TranslatorConfig] = None


class OutputConfig(BaseModel):
    """Output format configuration."""

    html_options: List[str] = Field(
        default_factory=list, description="HTML output options for pandoc"
    )
    pdf_options: List[str] = Field(
        default_factory=list, description="PDF output options for pandoc"
    )
    docx_options: List[str] = Field(
        default_factory=list, description="DOCX output options for pandoc"
    )
    slides_options: List[str] = Field(
        default_factory=list, description="Slides output options for pandoc"
    )


class WorkflowStepConfig(BaseModel):
    """Configuration for a workflow step."""

    name: str = Field(..., description="Name of the step")
    type: str = Field(
        default="prompt",
        description="Type of step (prompt, validation, output, etc.)",
    )
    prompt: Optional[str] = Field(
        default=None, description="Path to prompt template (for prompt steps)"
    )
    llm_model_alias: Optional[str] = Field(
        default=None, description="LLM model alias to use (for prompt steps)"
    )
    output_variable: Optional[str] = Field(
        default=None, description="Variable name to store output in"
    )
    output_format: Optional[str] = Field(
        default="raw", description="Output format (raw, list, json, html)"
    )
    transformation_rules: Optional[Dict[str, Any]] = Field(
        default=None, description="Rules for content transformation"
    )
    validators: Optional[List[str]] = Field(
        default=None, description="Validators to run (for validation steps)"
    )
    targets: Optional[List[str]] = Field(
        default=None, description="Targets to validate or remediate"
    )
    remediators: Optional[List[str]] = Field(
        default=None, description="Remediators to run (for remediation steps)"
    )
    formats: Optional[List[str]] = Field(
        default=None, description="Output formats to generate (for output steps)"
    )
    content_variable: Optional[str] = Field(
        default=None, description="Variable containing content to output"
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None, description="Metadata for output"
    )

    @model_validator(mode="after")
    def validate_step_type(self) -> "WorkflowStepConfig":
        """Validate that step has required fields for its type."""
        if self.type == "prompt" and not self.prompt:
            raise ValueError(f"Prompt steps require a 'prompt' field: {self.name}")
        if self.type == "validation" and not self.validators:
            raise ValueError(f"Validation steps require 'validators' field: {self.name}")
        if self.type == "output" and not self.formats:
            raise ValueError(f"Output steps require 'formats' field: {self.name}")
        return self


class WorkflowConfig(BaseModel):
    """Configuration for a workflow."""

    description: str = Field(..., description="Description of the workflow")
    steps: List[WorkflowStepConfig] = Field(
        default_factory=list, description="Steps in the workflow"
    )


class AppConfig(BaseModel):
    """Overall application configuration."""

    system: SystemConfig = Field(default_factory=SystemConfig)
    llm: LLMConfig = Field(...)
    prompts: PromptConfig = Field(default_factory=PromptConfig)
    validation: Optional[ValidationConfig] = None
    remediation: Optional[RemediationConfig] = None
    output: Optional[OutputConfig] = None
    workflows: Dict[str, WorkflowConfig] = Field(
        default_factory=dict, description="Available workflows"
    )

    @classmethod
    def from_file(cls, file_path: str) -> "AppConfig":
        """Load configuration from a YAML file."""
        import yaml

        with open(file_path, "r") as f:
            config_data = yaml.safe_load(f)
        return cls.model_validate(config_data)