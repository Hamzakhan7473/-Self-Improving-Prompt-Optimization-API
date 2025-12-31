"""API endpoints for production A/B testing and canary deployment."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from storage import get_db, PromptStorage
from models import PromptVersionResponse

router = APIRouter(prefix="/ab-testing", tags=["ab-testing"])


class ABTestConfig(BaseModel):
    """Configuration for A/B test."""
    prompt_id: str
    version_a_id: int = Field(..., description="Baseline version ID")
    version_b_id: int = Field(..., description="Candidate version ID")
    traffic_split: float = Field(0.5, ge=0.0, le=1.0, description="Traffic percentage for version B (0.0-1.0)")
    enabled: bool = True
    metadata: Optional[dict] = None


class ABTestResponse(BaseModel):
    """Response for A/B test selection."""
    selected_version_id: int
    selected_version: str
    test_id: Optional[str] = None
    is_canary: bool = False


@router.post("/config", status_code=201)
def create_ab_test_config(
    config: ABTestConfig,
    db: Session = Depends(get_db)
):
    """Create or update A/B test configuration."""
    storage = PromptStorage(db)
    
    # Verify both versions exist
    version_a = storage.get_version(config.version_a_id)
    version_b = storage.get_version(config.version_b_id)
    
    if not version_a or not version_b:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    
    if version_a.prompt_id != config.prompt_id or version_b.prompt_id != config.prompt_id:
        raise HTTPException(
            status_code=400,
            detail="Both versions must belong to the same prompt_id"
        )
    
    # Store config (in production, use Redis or database)
    # For now, return the config
    return {
        "config_id": f"{config.prompt_id}_{config.version_a_id}_{config.version_b_id}",
        "config": config.model_dump(),
        "message": "A/B test configuration created"
    }


@router.get("/select/{prompt_id}", response_model=ABTestResponse)
def select_version_for_ab_test(
    prompt_id: str,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Select a prompt version for A/B testing.
    
    This endpoint implements traffic splitting for A/B tests and canary deployments.
    Based on Langfuse's approach: https://langfuse.com/docs/prompt-management/features/a-b-testing
    """
    import random
    import hashlib
    
    storage = PromptStorage(db)
    
    # In production, fetch from Redis/database
    # For demo, we'll use a simple approach
    # Get active versions (could be multiple for A/B testing)
    versions = storage.list_versions(prompt_id=prompt_id, status=None)
    
    if not versions:
        raise HTTPException(status_code=404, detail=f"No versions found for prompt {prompt_id}")
    
    # Get active version (baseline)
    active_version = storage.get_active_version(prompt_id)
    
    if not active_version:
        # No active version, return latest
        latest = storage.get_latest_version(prompt_id)
        return ABTestResponse(
            selected_version_id=latest.id,
            selected_version=latest.version,
            is_canary=False
        )
    
    # Check for experimental versions (candidates for A/B testing)
    experimental_versions = [v for v in versions if v.status == "experimental"]
    
    if not experimental_versions:
        # No A/B test, return active version
        return ABTestResponse(
            selected_version_id=active_version.id,
            selected_version=active_version.version,
            is_canary=False
        )
    
    # A/B test exists - implement traffic splitting
    # Use consistent hashing based on user_id if provided
    if user_id:
        # Consistent assignment: same user always gets same version
        hash_value = int(hashlib.md5(f"{prompt_id}_{user_id}".encode()).hexdigest(), 16)
        use_experimental = (hash_value % 100) < 10  # 10% canary by default
    else:
        # Random assignment
        use_experimental = random.random() < 0.1  # 10% canary by default
    
    if use_experimental:
        # Select best experimental version (highest score or latest)
        selected = max(experimental_versions, key=lambda v: v.created_at)
        return ABTestResponse(
            selected_version_id=selected.id,
            selected_version=selected.version,
            test_id=f"{prompt_id}_ab_test",
            is_canary=True
        )
    else:
        # Use active version
        return ABTestResponse(
            selected_version_id=active_version.id,
            selected_version=active_version.version,
            test_id=f"{prompt_id}_ab_test",
            is_canary=False
        )


@router.get("/metrics/{prompt_id}")
def get_ab_test_metrics(
    prompt_id: str,
    db: Session = Depends(get_db)
):
    """Get A/B test metrics for a prompt."""
    storage = PromptStorage(db)
    from storage.evaluation_storage import EvaluationStorage
    
    eval_storage = EvaluationStorage(db)
    
    # Get all versions
    versions = storage.list_versions(prompt_id=prompt_id)
    active = storage.get_active_version(prompt_id)
    
    metrics = []
    for version in versions:
        # Get latest evaluation results
        # In production, you'd track real-time metrics (latency, cost, token usage)
        latest_results = eval_storage.get_latest_results(
            prompt_version_id=version.id,
            dataset_id="production"  # In production, use actual dataset tracking
        )
        
        aggregate = sum(r.score for r in latest_results.values()) / len(latest_results) if latest_results else 0.0
        
        metrics.append({
            "version_id": version.id,
            "version": version.version,
            "status": version.status,
            "is_active": active and active.id == version.id if active else False,
            "aggregate_score": aggregate,
            "dimension_scores": {dim: r.score for dim, r in latest_results.items()},
            "created_at": version.created_at.isoformat()
        })
    
    return {
        "prompt_id": prompt_id,
        "metrics": metrics,
        "note": "In production, include real-time metrics: latency, cost, token usage, error rates"
    }


