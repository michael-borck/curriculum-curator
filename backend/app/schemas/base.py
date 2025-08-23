"""
Base Pydantic model with camelCase serialization support
"""
from pydantic import BaseModel, ConfigDict


def snake_to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase for JSON serialization"""
    components = snake_str.split('_')
    # Keep the first component as-is, capitalize the rest
    return components[0] + ''.join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    """
    Base model that automatically converts snake_case field names to camelCase
    for JSON serialization while keeping Python code PEP8 compliant.

    - Output: Always camelCase in JSON
    - Input: Accepts both camelCase and snake_case
    - Python: Always snake_case internally
    """
    model_config = ConfigDict(
        # Convert snake_case to camelCase for JSON output
        alias_generator=snake_to_camel,
        # Accept both snake_case and camelCase on input
        populate_by_name=True,
        # Allow from ORM models
        from_attributes=True,
        # Use enum values in JSON
        use_enum_values=True,
        # Include fields even if they're None
        # (you can override this per model if needed)
        json_encoders={
            # Add any custom encoders here if needed
        }
    )
