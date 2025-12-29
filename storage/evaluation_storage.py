"""Storage operations for evaluation results."""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models import EvaluationResult, EvaluationDimension


class EvaluationStorage:
    """Storage for evaluation results."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_result(
        self,
        prompt_version_id: int,
        dataset_id: str,
        dimension: str,
        score: float,
        metadata: Optional[Dict] = None
    ) -> EvaluationResult:
        """Save an evaluation result."""
        result = EvaluationResult(
            prompt_version_id=prompt_version_id,
            dataset_id=dataset_id,
            dimension=dimension,
            score=score,
            metadata=metadata or {}
        )
        
        self.db.add(result)
        self.db.flush()
        return result
    
    def get_results(
        self,
        prompt_version_id: int,
        dataset_id: Optional[str] = None,
        dimension: Optional[str] = None
    ) -> List[EvaluationResult]:
        """Get evaluation results with optional filters."""
        query = self.db.query(EvaluationResult).filter(
            EvaluationResult.prompt_version_id == prompt_version_id
        )
        
        if dataset_id:
            query = query.filter(EvaluationResult.dataset_id == dataset_id)
        
        if dimension:
            query = query.filter(EvaluationResult.dimension == dimension)
        
        return query.order_by(desc(EvaluationResult.created_at)).all()
    
    def get_aggregate_scores(
        self,
        prompt_version_id: int,
        dataset_id: str
    ) -> Dict[str, float]:
        """Get aggregate scores per dimension for a prompt version."""
        results = self.db.query(
            EvaluationResult.dimension,
            func.avg(EvaluationResult.score).label('avg_score')
        ).filter(
            EvaluationResult.prompt_version_id == prompt_version_id,
            EvaluationResult.dataset_id == dataset_id
        ).group_by(EvaluationResult.dimension).all()
        
        return {dim: score for dim, score in results}
    
    def get_latest_results(
        self,
        prompt_version_id: int,
        dataset_id: str
    ) -> Dict[str, EvaluationResult]:
        """Get latest evaluation result for each dimension."""
        # Get the most recent evaluation timestamp
        latest_time = self.db.query(
            func.max(EvaluationResult.created_at)
        ).filter(
            EvaluationResult.prompt_version_id == prompt_version_id,
            EvaluationResult.dataset_id == dataset_id
        ).scalar()
        
        if not latest_time:
            return {}
        
        # Get all results from that timestamp
        results = self.db.query(EvaluationResult).filter(
            EvaluationResult.prompt_version_id == prompt_version_id,
            EvaluationResult.dataset_id == dataset_id,
            EvaluationResult.created_at == latest_time
        ).all()
        
        return {r.dimension: r for r in results}

