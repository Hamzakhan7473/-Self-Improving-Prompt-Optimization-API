"""Audit logging and interpretability tools."""
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import json


class AuditEventType(str, Enum):
    """Types of audit events."""
    PROMPT_CREATED = "prompt_created"
    PROMPT_PROMOTED = "prompt_promoted"
    PROMPT_DEPRECATED = "prompt_deprecated"
    EVALUATION_RUN = "evaluation_run"
    EXPERIMENT_RUN = "experiment_run"
    IMPROVEMENT_GENERATED = "improvement_generated"
    REGRESSION_DETECTED = "regression_detected"
    GUARDRAIL_FAILED = "guardrail_failed"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


class AuditLogger:
    """Logger for audit trail and interpretability."""
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
    
    def log(
        self,
        event_type: AuditEventType,
        details: Dict[str, Any],
        prompt_version_id: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Log an audit event."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type.value,
            'prompt_version_id': prompt_version_id,
            'user_id': user_id,
            'details': details
        }
        self.events.append(event)
    
    def log_prompt_change(
        self,
        from_version_id: int,
        to_version_id: int,
        change_summary: str,
        metrics_delta: Optional[Dict[str, float]] = None
    ) -> None:
        """Log a prompt version change with interpretable details."""
        self.log(
            AuditEventType.PROMPT_PROMOTED,
            {
                'from_version_id': from_version_id,
                'to_version_id': to_version_id,
                'change_summary': change_summary,
                'metrics_delta': metrics_delta,
                'human_readable': f"Prompt version {to_version_id} promoted from {from_version_id}. {change_summary}"
            },
            prompt_version_id=to_version_id
        )
    
    def log_regression(
        self,
        version_id: int,
        dimension: str,
        baseline_score: float,
        candidate_score: float,
        delta: float
    ) -> None:
        """Log a detected regression."""
        self.log(
            AuditEventType.REGRESSION_DETECTED,
            {
                'version_id': version_id,
                'dimension': dimension,
                'baseline_score': baseline_score,
                'candidate_score': candidate_score,
                'delta': delta,
                'human_readable': f"Regression detected in {dimension}: {baseline_score:.3f} → {candidate_score:.3f} (Δ{delta:+.3f})"
            },
            prompt_version_id=version_id
        )
    
    def log_guardrail_failure(
        self,
        version_id: int,
        guardrail_name: str,
        reason: str,
        threshold: Optional[float] = None,
        actual_value: Optional[float] = None
    ) -> None:
        """Log a guardrail failure."""
        details = {
            'guardrail_name': guardrail_name,
            'reason': reason,
            'human_readable': f"Guardrail '{guardrail_name}' failed: {reason}"
        }
        if threshold is not None:
            details['threshold'] = threshold
        if actual_value is not None:
            details['actual_value'] = actual_value
            details['human_readable'] += f" (threshold: {threshold}, actual: {actual_value})"
        
        self.log(
            AuditEventType.GUARDRAIL_FAILED,
            details,
            prompt_version_id=version_id
        )
    
    def get_audit_trail(
        self,
        prompt_version_id: Optional[int] = None,
        event_type: Optional[AuditEventType] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get audit trail with optional filters."""
        events = self.events
        
        if prompt_version_id:
            events = [e for e in events if e.get('prompt_version_id') == prompt_version_id]
        
        if event_type:
            events = [e for e in events if e['event_type'] == event_type.value]
        
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_interpretable_explanation(
        self,
        prompt_version_id: int
    ) -> Dict[str, Any]:
        """Generate human-readable explanation of prompt changes."""
        events = self.get_audit_trail(prompt_version_id=prompt_version_id)
        
        explanations = []
        regressions = []
        improvements = []
        
        for event in events:
            if 'human_readable' in event.get('details', {}):
                explanations.append(event['details']['human_readable'])
            
            if event['event_type'] == AuditEventType.REGRESSION_DETECTED:
                regressions.append(event['details'])
            
            if event['event_type'] == AuditEventType.PROMPT_PROMOTED:
                if 'metrics_delta' in event['details']:
                    delta = event['details']['metrics_delta']
                    for dim, value in delta.items():
                        if value > 0:
                            improvements.append(f"{dim}: +{value:.3f}")
        
        return {
            'prompt_version_id': prompt_version_id,
            'summary': ' '.join(explanations[-5:]),  # Last 5 events
            'regressions': regressions,
            'improvements': improvements,
            'total_events': len(events)
        }


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

