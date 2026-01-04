"""Utilities for prompt template rendering."""
from typing import Dict, Any, Set
import re


def extract_variables(template: str) -> Set[str]:
    """Extract variable names from a prompt template."""
    pattern = r'\{([^}]+)\}'
    matches = re.findall(pattern, template)
    return set(matches)


def render_prompt(template: str, variables: Dict[str, Any]) -> str:
    """Render a prompt template with variables."""
    try:
        return template.format(**variables)
    except KeyError as e:
        missing = str(e).strip("'")
        raise ValueError(f"Missing required variable: {missing}")
    except Exception as e:
        raise ValueError(f"Error rendering prompt: {str(e)}")


def validate_variables(template: str, provided: Dict[str, Any]) -> tuple[bool, Set[str]]:
    """Validate that all required variables are provided."""
    required = extract_variables(template)
    provided_set = set(provided.keys())
    missing = required - provided_set
    return len(missing) == 0, missing



