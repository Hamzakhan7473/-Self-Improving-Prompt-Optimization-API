"""Storage operations for experiments."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import Experiment


class ExperimentStorage:
    """Storage for experiments."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_experiment(
        self,
        baseline_version_id: int,
        candidate_version_id: int,
        dataset_id: str,
        metrics: dict,
        improvement_rationale: Optional[str] = None,
        promoted: bool = False
    ) -> Experiment:
        """Create a new experiment record."""
        experiment = Experiment(
            baseline_version_id=baseline_version_id,
            candidate_version_id=candidate_version_id,
            dataset_id=dataset_id,
            metrics=metrics,
            improvement_rationale=improvement_rationale,
            promoted=promoted
        )
        
        self.db.add(experiment)
        self.db.flush()
        return experiment
    
    def get_experiment(self, experiment_id: int) -> Optional[Experiment]:
        """Get experiment by ID."""
        return self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
    
    def list_experiments(
        self,
        prompt_id: Optional[str] = None,
        promoted: Optional[bool] = None
    ) -> List[Experiment]:
        """List experiments with optional filters."""
        from models import PromptVersion
        
        query = self.db.query(Experiment)
        
        if prompt_id:
            query = query.join(
                PromptVersion,
                Experiment.baseline_version_id == PromptVersion.id
            ).filter(PromptVersion.prompt_id == prompt_id)
        
        if promoted is not None:
            query = query.filter(Experiment.promoted == promoted)
        
        return query.order_by(desc(Experiment.created_at)).all()
    
    def mark_promoted(self, experiment_id: int):
        """Mark an experiment as promoted."""
        experiment = self.get_experiment(experiment_id)
        if experiment:
            experiment.promoted = True

