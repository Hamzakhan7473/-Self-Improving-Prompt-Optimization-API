"""API endpoints for self-improvement."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from models import ExperimentResult
from storage import get_db, PromptStorage, EvaluationStorage, ExperimentStorage
from evaluation.evaluator import Evaluator
from evaluation.dataset import DatasetLoader
from improvement.analyzer import FailureAnalyzer
from improvement.generator import ImprovementGenerator
from improvement.experimenter import ExperimentRunner
from improvement.promoter import PromptPromoter

router = APIRouter(prefix="/improvement", tags=["improvement"])


@router.post("/analyze/{version_id}")
def analyze_failures(
    version_id: int,
    dataset_data: dict,
    db: Session = Depends(get_db)
):
    """Analyze failure cases for a prompt version."""
    storage = PromptStorage(db)
    eval_storage = EvaluationStorage(db)
    
    prompt_version = storage.get_version(version_id)
    if not prompt_version:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    
    # Load dataset and evaluate
    dataset = DatasetLoader.load_from_dict(dataset_data)
    evaluator = Evaluator(storage, eval_storage)
    evaluation_result = evaluator.evaluate(
        prompt_version_id=version_id,
        dataset=dataset
    )
    
    # Analyze failures
    analyzer = FailureAnalyzer(evaluator)
    analysis = analyzer.analyze_failures(evaluation_result, dataset)
    
    return {
        "prompt_version_id": version_id,
        "evaluation_result": evaluation_result.model_dump(),
        "failure_analysis": analysis
    }


@router.post("/generate-candidates/{version_id}")
def generate_improvements(
    version_id: int,
    dataset_data: dict,
    max_candidates: int = 5,
    db: Session = Depends(get_db)
):
    """Generate candidate prompt improvements."""
    storage = PromptStorage(db)
    eval_storage = EvaluationStorage(db)
    
    prompt_version = storage.get_version(version_id)
    if not prompt_version:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    
    # Load dataset and evaluate
    dataset = DatasetLoader.load_from_dict(dataset_data)
    evaluator = Evaluator(storage, eval_storage)
    evaluation_result = evaluator.evaluate(
        prompt_version_id=version_id,
        dataset=dataset
    )
    
    # Analyze failures
    analyzer = FailureAnalyzer(evaluator)
    failure_analysis = analyzer.analyze_failures(evaluation_result, dataset)
    
    # Generate candidates
    generator = ImprovementGenerator()
    candidates = generator.generate_candidates(
        current_template=prompt_version.template,
        failure_analysis=failure_analysis,
        max_candidates=max_candidates
    )
    
    return {
        "prompt_version_id": version_id,
        "current_template": prompt_version.template,
        "failure_analysis": failure_analysis,
        "candidates": candidates
    }


@router.post("/experiment", response_model=ExperimentResult)
def run_experiment(
    baseline_version_id: int,
    candidate_version_id: int,
    dataset_data: dict,
    db: Session = Depends(get_db)
):
    """Run A/B experiment between two prompt versions."""
    storage = PromptStorage(db)
    eval_storage = EvaluationStorage(db)
    experiment_storage = ExperimentStorage(db)
    
    # Verify versions exist
    baseline = storage.get_version(baseline_version_id)
    candidate = storage.get_version(candidate_version_id)
    
    if not baseline or not candidate:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    
    # Load dataset
    dataset = DatasetLoader.load_from_dict(dataset_data)
    
    # Run experiment
    evaluator = Evaluator(storage, eval_storage)
    experimenter = ExperimentRunner(evaluator, storage, experiment_storage)
    result = experimenter.run_experiment(
        baseline_version_id=baseline_version_id,
        candidate_version_id=candidate_version_id,
        dataset=dataset
    )
    
    return result


@router.post("/promote/{experiment_id}")
def promote_candidate(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    """Promote a candidate version based on experiment results."""
    storage = PromptStorage(db)
    eval_storage = EvaluationStorage(db)
    experiment_storage = ExperimentStorage(db)
    
    experiment = experiment_storage.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Get experiment result
    evaluator = Evaluator(storage, eval_storage)
    experimenter = ExperimentRunner(evaluator, storage, experiment_storage)
    
    # Re-run experiment to get full result (in production, you'd cache this)
    # For now, we'll use the stored metrics
    from models import ExperimentResult
    experiment_result = ExperimentResult(
        experiment_id=experiment.id,
        baseline_version=storage.get_version(experiment.baseline_version_id).version,
        candidate_version=storage.get_version(experiment.candidate_version_id).version,
        baseline_metrics=experiment.metrics.get("baseline", {}),
        candidate_metrics=experiment.metrics.get("candidate", {}),
        improvement_delta=experiment.metrics.get("delta", {}),
        promoted=False,
        promotion_rationale=None
    )
    
    # Check if should promote
    promoter = PromptPromoter(storage, experiment_storage, eval_storage)
    
    # Load dataset for guardrails (simplified - in production, store dataset_id)
    # For now, we'll skip the dataset check in promotion
    should_promote, rationale = promoter.should_promote(experiment_result, None)
    
    if should_promote:
        promoter.promote(experiment_id, experiment.candidate_version_id)
        return {
            "promoted": True,
            "rationale": rationale,
            "candidate_version_id": experiment.candidate_version_id
        }
    else:
        return {
            "promoted": False,
            "rationale": rationale,
            "reason": "Guardrails not met"
        }


@router.post("/self-improve/{version_id}")
def self_improve(
    version_id: int,
    dataset_data: dict,
    auto_promote: bool = False,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Run full self-improvement loop:
    1. Evaluate current version
    2. Analyze failures
    3. Generate candidates
    4. Run experiments
    5. Optionally promote best candidate
    """
    storage = PromptStorage(db)
    eval_storage = EvaluationStorage(db)
    experiment_storage = ExperimentStorage(db)
    
    prompt_version = storage.get_version(version_id)
    if not prompt_version:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    
    # Load dataset
    dataset = DatasetLoader.load_from_dict(dataset_data)
    
    # Step 1: Evaluate
    evaluator = Evaluator(storage, eval_storage)
    evaluation_result = evaluator.evaluate(
        prompt_version_id=version_id,
        dataset=dataset
    )
    
    # Step 2: Analyze failures
    analyzer = FailureAnalyzer(evaluator)
    failure_analysis = analyzer.analyze_failures(evaluation_result, dataset)
    
    # Step 3: Generate candidates
    generator = ImprovementGenerator()
    candidates = generator.generate_candidates(
        current_template=prompt_version.template,
        failure_analysis=failure_analysis
    )
    
    # Step 4: Create candidate versions and run experiments
    experiment_results = []
    promoter = PromptPromoter(storage, experiment_storage, eval_storage)
    
    for candidate_data in candidates:
        # Create candidate version
        candidate_version = storage.create_version(
            prompt_id=prompt_version.prompt_id,
            template=candidate_data["template"],
            schema_definition=prompt_version.schema_definition,
            metadata={
                **(prompt_version.metadata or {}),
                "improvement_rationale": candidate_data.get("rationale", "")
            },
            parent_version_id=version_id,
            status="experimental"
        )
        
        # Run experiment
        experimenter = ExperimentRunner(evaluator, storage, experiment_storage)
        experiment_result = experimenter.run_experiment(
            baseline_version_id=version_id,
            candidate_version_id=candidate_version.id,
            dataset=dataset
        )
        
        # Check promotion
        should_promote, rationale = promoter.should_promote(experiment_result, dataset)
        experiment_result.promoted = should_promote
        experiment_result.promotion_rationale = rationale
        
        experiment_results.append({
            "candidate_version_id": candidate_version.id,
            "experiment": experiment_result.model_dump(),
            "should_promote": should_promote
        })
    
    # Step 5: Promote best candidate if auto_promote and guardrails met
    promoted_version = None
    if auto_promote:
        # Find best candidate
        best_candidate = max(
            experiment_results,
            key=lambda x: x["experiment"]["candidate_metrics"].get("aggregate", 0.0)
        )
        
        if best_candidate["should_promote"]:
            promoter.promote(
                best_candidate["experiment"]["experiment_id"],
                best_candidate["candidate_version_id"]
            )
            promoted_version = best_candidate["candidate_version_id"]
    
    return {
        "baseline_version_id": version_id,
        "failure_analysis": failure_analysis,
        "candidates_generated": len(candidates),
        "experiments": experiment_results,
        "promoted_version_id": promoted_version,
        "auto_promoted": auto_promote and promoted_version is not None
    }

