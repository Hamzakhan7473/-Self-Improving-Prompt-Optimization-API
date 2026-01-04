"""API endpoints for prompt management."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import (
    PromptTemplate,
    PromptVersionResponse,
    PromptDiff,
    ChangelogEntry
)
from storage import get_db, PromptStorage
from utils.diff_utils import compute_prompt_diff, compute_schema_diff

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/", response_model=PromptVersionResponse, status_code=201)
def create_prompt(
    prompt: PromptTemplate,
    db: Session = Depends(get_db)
):
    """Create a new prompt version."""
    storage = PromptStorage(db)
    
    # Check if parent version exists
    parent_version_id = None
    if prompt.parent_version:
        parent = storage.get_version_by_prompt_and_version(
            prompt.prompt_id,
            prompt.parent_version
        )
        if not parent:
            raise HTTPException(
                status_code=404,
                detail=f"Parent version {prompt.parent_version} not found"
            )
        parent_version_id = parent.id
    
    version = storage.create_version(
        prompt_id=prompt.prompt_id,
        template=prompt.template,
        schema_definition=prompt.schema_definition,
        metadata=prompt.metadata,
        parent_version_id=parent_version_id
    )
    
    return PromptVersionResponse.from_orm(version)


@router.get("/", response_model=List[PromptVersionResponse])
def list_prompts(
    prompt_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List prompt versions."""
    from models import PromptStatus
    
    storage = PromptStorage(db)
    status_enum = PromptStatus(status) if status else None
    versions = storage.list_versions(prompt_id=prompt_id, status=status_enum)
    
    return [PromptVersionResponse.from_orm(v) for v in versions]


@router.get("/{prompt_id}/versions", response_model=List[PromptVersionResponse])
def list_versions(
    prompt_id: str,
    db: Session = Depends(get_db)
):
    """List all versions of a prompt."""
    storage = PromptStorage(db)
    versions = storage.list_versions(prompt_id=prompt_id)
    
    return [PromptVersionResponse.from_orm(v) for v in versions]


@router.get("/{prompt_id}/active", response_model=PromptVersionResponse)
def get_active_version(
    prompt_id: str,
    db: Session = Depends(get_db)
):
    """Get active version of a prompt."""
    storage = PromptStorage(db)
    version = storage.get_active_version(prompt_id)
    
    if not version:
        raise HTTPException(
            status_code=404,
            detail=f"No active version found for prompt {prompt_id}"
        )
    
    return PromptVersionResponse.from_orm(version)


@router.get("/versions/{version_id}", response_model=PromptVersionResponse)
def get_version(
    version_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific prompt version."""
    storage = PromptStorage(db)
    version = storage.get_version(version_id)
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return PromptVersionResponse.from_orm(version)


@router.get("/versions/{version_id}/lineage", response_model=List[PromptVersionResponse])
def get_lineage(
    version_id: int,
    db: Session = Depends(get_db)
):
    """Get lineage (ancestors) of a prompt version."""
    storage = PromptStorage(db)
    lineage = storage.get_lineage(version_id)
    
    if not lineage:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return [PromptVersionResponse.from_orm(v) for v in lineage]


@router.get("/versions/{from_id}/diff/{to_id}", response_model=PromptDiff)
def get_diff(
    from_id: int,
    to_id: int,
    db: Session = Depends(get_db)
):
    """Get diff between two prompt versions."""
    storage = PromptStorage(db)
    
    from_version = storage.get_version(from_id)
    to_version = storage.get_version(to_id)
    
    if not from_version or not to_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    template_diff = compute_prompt_diff(from_version.template, to_version.template)
    schema_diff = compute_schema_diff(from_version.schema_definition, to_version.schema_definition)
    
    # Simple metadata diff
    metadata_diff = None
    if from_version.meta_data != to_version.meta_data:
        metadata_diff = {
            "old": from_version.meta_data,
            "new": to_version.meta_data
        }
    
    return PromptDiff(
        from_version=from_version.version,
        to_version=to_version.version,
        template_diff=template_diff,
        schema_diff=schema_diff,
        metadata_diff=metadata_diff
    )


@router.get("/{prompt_id}/changelog", response_model=List[ChangelogEntry])
def get_changelog(
    prompt_id: str,
    db: Session = Depends(get_db)
):
    """Get changelog for a prompt."""
    storage = PromptStorage(db)
    versions = storage.list_versions(prompt_id=prompt_id)
    
    changelog = []
    for version in versions:
        # Get metrics if available
        from storage.evaluation_storage import EvaluationStorage
        eval_storage = EvaluationStorage(db)
        
        # Get latest metrics (simplified - in production, you'd want more sophisticated tracking)
        metrics_delta = None
        
        if version.parent_version_id:
            parent = storage.get_version(version.parent_version_id)
            if parent:
                # Compare metrics (simplified)
                metrics_delta = {}
        
        changelog.append(ChangelogEntry(
            version=version.version,
            timestamp=version.created_at,
            changes={
                "status": version.status,
                "template_length": len(version.template),
                "has_schema": version.schema_definition is not None
            },
            metrics_delta=metrics_delta
        ))
    
    return changelog


@router.post("/versions/{version_id}/promote", response_model=PromptVersionResponse)
def promote_version(
    version_id: int,
    db: Session = Depends(get_db)
):
    """Promote a version to active status."""
    storage = PromptStorage(db)
    
    try:
        version = storage.promote_version(version_id)
        return PromptVersionResponse.from_orm(version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

