"""API endpoints for audit trail and interpretability."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from storage import get_db
from utils.audit import get_audit_logger, AuditEventType

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/trail/{prompt_version_id}")
def get_audit_trail(
    prompt_version_id: int,
    event_type: Optional[str] = None,
    limit: Optional[int] = 100,
    db: Session = Depends(get_db)
):
    """Get audit trail for a prompt version."""
    audit_logger = get_audit_logger()
    
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
    
    trail = audit_logger.get_audit_trail(
        prompt_version_id=prompt_version_id,
        event_type=event_type_enum,
        limit=limit
    )
    
    return {
        "prompt_version_id": prompt_version_id,
        "events": trail,
        "total_events": len(trail)
    }


@router.get("/explanation/{prompt_version_id}")
def get_interpretable_explanation(
    prompt_version_id: int,
    db: Session = Depends(get_db)
):
    """Get human-readable explanation of prompt changes and decisions."""
    audit_logger = get_audit_logger()
    
    explanation = audit_logger.get_interpretable_explanation(prompt_version_id)
    
    return explanation


@router.get("/regressions/{prompt_version_id}")
def get_regressions(
    prompt_version_id: int,
    db: Session = Depends(get_db)
):
    """Get all regressions detected for a prompt version."""
    audit_logger = get_audit_logger()
    
    events = audit_logger.get_audit_trail(
        prompt_version_id=prompt_version_id,
        event_type=AuditEventType.REGRESSION_DETECTED
    )
    
    regressions = [e['details'] for e in events]
    
    return {
        "prompt_version_id": prompt_version_id,
        "regressions": regressions,
        "count": len(regressions)
    }


@router.get("/cache/stats")
def get_cache_stats():
    """Get cache statistics."""
    from utils.cache import get_cache
    
    cache = get_cache()
    stats = cache.stats()
    
    return stats


@router.post("/cache/clear")
def clear_cache():
    """Clear the LLM response cache."""
    from utils.cache import get_cache
    
    cache = get_cache()
    cache.clear()
    
    return {"message": "Cache cleared successfully"}

