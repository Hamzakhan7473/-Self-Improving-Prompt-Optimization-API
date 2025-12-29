"""API endpoints for evaluation."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import EvaluationRequest, EvaluationResponse, EvaluationDimension
from storage import get_db, PromptStorage, EvaluationStorage
from evaluation.evaluator import Evaluator
from evaluation.dataset import DatasetLoader

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/", response_model=EvaluationResponse)
def evaluate_prompt(
    request: EvaluationRequest,
    dataset_data: dict,
    db: Session = Depends(get_db)
):
    """Evaluate a prompt version on a dataset."""
    storage = PromptStorage(db)
    eval_storage = EvaluationStorage(db)
    
    # Verify prompt version exists
    prompt_version = storage.get_version(request.prompt_version_id)
    if not prompt_version:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    
    # Load dataset
    dataset = DatasetLoader.load_from_dict(dataset_data)
    
    # Run evaluation
    evaluator = Evaluator(storage, eval_storage)
    result = evaluator.evaluate(
        prompt_version_id=request.prompt_version_id,
        dataset=dataset,
        dimensions=request.dimensions
    )
    
    return result


@router.post("/from-file", response_model=EvaluationResponse)
def evaluate_from_file(
    request: EvaluationRequest,
    dataset_file_path: str,
    db: Session = Depends(get_db)
):
    """Evaluate a prompt version using a dataset file."""
    storage = PromptStorage(db)
    eval_storage = EvaluationStorage(db)
    
    # Verify prompt version exists
    prompt_version = storage.get_version(request.prompt_version_id)
    if not prompt_version:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    
    # Load dataset
    dataset = DatasetLoader.load_from_file(dataset_file_path)
    
    # Run evaluation
    evaluator = Evaluator(storage, eval_storage)
    result = evaluator.evaluate(
        prompt_version_id=request.prompt_version_id,
        dataset=dataset,
        dimensions=request.dimensions
    )
    
    return result


@router.get("/versions/{version_id}/results", response_model=List[dict])
def get_evaluation_results(
    version_id: int,
    dataset_id: Optional[str] = None,
    dimension: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get evaluation results for a prompt version."""
    eval_storage = EvaluationStorage(db)
    results = eval_storage.get_results(
        prompt_version_id=version_id,
        dataset_id=dataset_id,
        dimension=dimension
    )
    
    return [
        {
            "id": r.id,
            "dataset_id": r.dataset_id,
            "dimension": r.dimension,
            "score": r.score,
            "metadata": r.metadata,
            "created_at": r.created_at.isoformat()
        }
        for r in results
    ]


@router.get("/versions/{version_id}/aggregate", response_model=dict)
def get_aggregate_scores(
    version_id: int,
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """Get aggregate evaluation scores for a prompt version."""
    eval_storage = EvaluationStorage(db)
    scores = eval_storage.get_aggregate_scores(
        prompt_version_id=version_id,
        dataset_id=dataset_id
    )
    
    return {
        "prompt_version_id": version_id,
        "dataset_id": dataset_id,
        "scores": scores,
        "aggregate": sum(scores.values()) / len(scores) if scores else 0.0
    }

