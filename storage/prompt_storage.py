"""Storage operations for prompt versions."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import PromptVersion, PromptStatus, PromptVersionResponse


class PromptStorage:
    """Storage for prompt versions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_version(
        self,
        prompt_id: str,
        template: str,
        schema_definition: Optional[dict] = None,
        metadata: Optional[dict] = None,
        parent_version_id: Optional[int] = None,
        status: PromptStatus = PromptStatus.DRAFT
    ) -> PromptVersion:
        """Create a new prompt version."""
        # Get next version number
        latest = self.get_latest_version(prompt_id)
        if latest:
            version_parts = latest.version.split(".")
            try:
                version_num = int(version_parts[-1]) + 1
                version = ".".join(version_parts[:-1] + [str(version_num)])
            except ValueError:
                version = f"{latest.version}.1"
        else:
            version = "1.0.0"
        
        prompt_version = PromptVersion(
            prompt_id=prompt_id,
            version=version,
            template=template,
            schema_definition=schema_definition,
            meta_data=metadata or {},
            parent_version_id=parent_version_id,
            status=status.value
        )
        
        self.db.add(prompt_version)
        self.db.flush()
        return prompt_version
    
    def get_version(self, version_id: int) -> Optional[PromptVersion]:
        """Get prompt version by ID."""
        return self.db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
    
    def get_version_by_prompt_and_version(
        self,
        prompt_id: str,
        version: str
    ) -> Optional[PromptVersion]:
        """Get prompt version by prompt ID and version string."""
        return self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version == version
        ).first()
    
    def get_latest_version(self, prompt_id: str) -> Optional[PromptVersion]:
        """Get latest version of a prompt."""
        return self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id
        ).order_by(desc(PromptVersion.created_at)).first()
    
    def get_active_version(self, prompt_id: str) -> Optional[PromptVersion]:
        """Get active version of a prompt."""
        return self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.status == PromptStatus.ACTIVE.value
        ).order_by(desc(PromptVersion.promoted_at)).first()
    
    def list_versions(
        self,
        prompt_id: Optional[str] = None,
        status: Optional[PromptStatus] = None
    ) -> List[PromptVersion]:
        """List prompt versions with optional filters."""
        query = self.db.query(PromptVersion)
        
        if prompt_id:
            query = query.filter(PromptVersion.prompt_id == prompt_id)
        
        if status:
            query = query.filter(PromptVersion.status == status.value)
        
        return query.order_by(desc(PromptVersion.created_at)).all()
    
    def promote_version(self, version_id: int) -> PromptVersion:
        """Promote a version to active status."""
        version = self.get_version(version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found")
        
        # Deprecate other active versions
        self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == version.prompt_id,
            PromptVersion.status == PromptStatus.ACTIVE.value
        ).update({"status": PromptStatus.DEPRECATED.value})
        
        # Promote this version
        version.status = PromptStatus.ACTIVE.value
        version.promoted_at = datetime.utcnow()
        
        return version
    
    def get_lineage(self, version_id: int) -> List[PromptVersion]:
        """Get lineage of a prompt version (all ancestors)."""
        version = self.get_version(version_id)
        if not version:
            return []
        
        lineage = [version]
        current = version
        
        while current.parent_version_id:
            current = self.get_version(current.parent_version_id)
            if current:
                lineage.append(current)
            else:
                break
        
        return list(reversed(lineage))

