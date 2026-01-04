"""Utilities for computing diffs between prompt versions."""
from typing import Dict, Any, Optional
import difflib
import json


def compute_prompt_diff(old_template: str, new_template: str) -> str:
    """Compute a diff between two prompt templates."""
    old_lines = old_template.splitlines(keepends=True)
    new_lines = new_template.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="old",
        tofile="new",
        lineterm=""
    )
    
    return "".join(diff)


def compute_schema_diff(old_schema: Optional[Dict[str, Any]], new_schema: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Compute diff between two JSON schemas."""
    if old_schema is None and new_schema is None:
        return None
    
    if old_schema is None:
        return {"added": new_schema}
    
    if new_schema is None:
        return {"removed": old_schema}
    
    # Simple diff: find added, removed, and changed keys
    old_keys = set(_flatten_dict(old_schema).keys())
    new_keys = set(_flatten_dict(new_schema).keys())
    
    added = {k: _get_nested_value(new_schema, k) for k in new_keys - old_keys}
    removed = {k: _get_nested_value(old_schema, k) for k in old_keys - new_keys}
    changed = {}
    
    for key in old_keys & new_keys:
        old_val = _get_nested_value(old_schema, key)
        new_val = _get_nested_value(new_schema, key)
        if old_val != new_val:
            changed[key] = {"old": old_val, "new": new_val}
    
    diff = {}
    if added:
        diff["added"] = added
    if removed:
        diff["removed"] = removed
    if changed:
        diff["changed"] = changed
    
    return diff if diff else None


def _flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _get_nested_value(d: Dict[str, Any], key: str, sep: str = ".") -> Any:
    """Get value from nested dictionary using dot notation."""
    keys = key.split(sep)
    value = d
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
            if value is None:
                return None
        else:
            return None
    return value



