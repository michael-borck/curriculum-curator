from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class PluginResult(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[list] = None

class ValidatorPlugin(ABC):
    """Base class for content validators"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    async def validate(self, content: str, metadata: Dict[str, Any]) -> PluginResult:
        """Validate content and return results"""
        pass

class RemediatorPlugin(ABC):
    """Base class for content remediators"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    async def remediate(self, content: str, issues: list) -> PluginResult:
        """Remediate content based on identified issues"""
        pass