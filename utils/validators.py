"""Validators for deterministic evaluation."""
from typing import Any, Dict, Optional, List
import re
import jsonschema
from abc import ABC, abstractmethod


class BaseValidator(ABC):
    """Base class for validators."""
    
    @abstractmethod
    def validate(self, output: str, expected: Any = None) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate output.
        
        Returns:
            (is_valid, details_dict)
        """
        pass


class JSONSchemaValidator(BaseValidator):
    """JSON schema validator."""
    
    def validate(self, output: str, expected: Any = None) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Validate output against JSON schema."""
        import json
        
        if expected is None:
            return True, {"message": "No schema provided"}
        
        try:
            # Parse JSON
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                start = output.find("{")
                end = output.rfind("}") + 1
                if start >= 0 and end > start:
                    parsed = json.loads(output[start:end])
                else:
                    return False, {"error": "Invalid JSON", "output": output[:200]}
            
            # Validate against schema
            jsonschema.validate(instance=parsed, schema=expected)
            return True, {"validated": True}
        
        except jsonschema.ValidationError as e:
            return False, {
                "error": "Schema validation failed",
                "message": str(e),
                "path": list(e.path) if e.path else []
            }
        except Exception as e:
            return False, {"error": str(e)}


class RegexValidator(BaseValidator):
    """Regex pattern validator."""
    
    def validate(self, output: str, expected: Any = None) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Validate output against regex pattern."""
        if expected is None:
            return True, {"message": "No pattern provided"}
        
        pattern = expected if isinstance(expected, str) else expected.get("pattern", "")
        flags = 0
        if isinstance(expected, dict) and expected.get("case_insensitive", False):
            flags = re.IGNORECASE
        
        try:
            match = re.search(pattern, output, flags)
            if match:
                return True, {"matched": True, "groups": match.groups()}
            else:
                return False, {"matched": False, "pattern": pattern}
        except re.error as e:
            return False, {"error": f"Invalid regex pattern: {str(e)}"}


class ConstraintValidator(BaseValidator):
    """Constraint-based validator (e.g., length, contains, etc.)."""
    
    def validate(self, output: str, expected: Any = None) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Validate output against constraints."""
        if expected is None:
            return True, {"message": "No constraints provided"}
        
        constraints = expected if isinstance(expected, dict) else {}
        violations = []
        
        # Length constraints
        if "min_length" in constraints:
            if len(output) < constraints["min_length"]:
                violations.append(f"Length {len(output)} < min_length {constraints['min_length']}")
        
        if "max_length" in constraints:
            if len(output) > constraints["max_length"]:
                violations.append(f"Length {len(output)} > max_length {constraints['max_length']}")
        
        # Contains constraints
        if "must_contain" in constraints:
            required = constraints["must_contain"]
            if isinstance(required, str):
                required = [required]
            for item in required:
                if item not in output:
                    violations.append(f"Missing required content: {item}")
        
        if "must_not_contain" in constraints:
            forbidden = constraints["must_not_contain"]
            if isinstance(forbidden, str):
                forbidden = [forbidden]
            for item in forbidden:
                if item in output:
                    violations.append(f"Contains forbidden content: {item}")
        
        if violations:
            return False, {"violations": violations}
        
        return True, {"validated": True}


class ValidatorRegistry:
    """Registry for validators."""
    
    _validators: Dict[str, BaseValidator] = {
        "json_schema": JSONSchemaValidator(),
        "regex": RegexValidator(),
        "constraint": ConstraintValidator(),
    }
    
    @classmethod
    def register(cls, name: str, validator: BaseValidator):
        """Register a validator."""
        cls._validators[name] = validator
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseValidator]:
        """Get a validator by name."""
        return cls._validators.get(name)
    
    @classmethod
    def validate(cls, validator_type: str, output: str, expected: Any = None) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Validate using a registered validator."""
        validator = cls.get(validator_type)
        if validator is None:
            raise ValueError(f"Unknown validator type: {validator_type}")
        return validator.validate(output, expected)



