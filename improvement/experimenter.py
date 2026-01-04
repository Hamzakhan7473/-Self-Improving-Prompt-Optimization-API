"""A/B experiment runner."""
from typing import Dict, Any, Optional
from storage.experiment_storage import ExperimentStorage
from storage.prompt_storage import PromptStorage
from evaluation.evaluator import Evaluator
from evaluation.dataset import Dataset
from models import ExperimentResult


class ExperimentRunner:
    """Runs A/B experiments between prompt versions."""
    
    def __init__(
        self,
        evaluator: Evaluator,
        prompt_storage: PromptStorage,
        experiment_storage: ExperimentStorage
    ):
        self.evaluator = evaluator
        self.prompt_storage = prompt_storage
        self.experiment_storage = experiment_storage
    
    def run_experiment(
        self,
        baseline_version_id: int,
        candidate_version_id: int,
        dataset: Dataset
    ) -> ExperimentResult:
        """
        Run A/B experiment comparing baseline and candidate.
        
        Returns experiment result with metrics comparison.
        """
        # Evaluate both versions
        baseline_result = self.evaluator.evaluate(
            prompt_version_id=baseline_version_id,
            dataset=dataset
        )
        
        candidate_result = self.evaluator.evaluate(
            prompt_version_id=candidate_version_id,
            dataset=dataset
        )
        
        # Compute metrics
        baseline_metrics = self._compute_metrics(baseline_result)
        candidate_metrics = self._compute_metrics(candidate_result)
        
        # Compute deltas
        improvement_delta = {
            dim: candidate_metrics.get(dim, 0.0) - baseline_metrics.get(dim, 0.0)
            for dim in set(list(baseline_metrics.keys()) + list(candidate_metrics.keys()))
        }
        
        # Create experiment record
        experiment = self.experiment_storage.create_experiment(
            baseline_version_id=baseline_version_id,
            candidate_version_id=candidate_version_id,
            dataset_id=dataset.dataset_id,
            metrics={
                "baseline": baseline_metrics,
                "candidate": candidate_metrics,
                "delta": improvement_delta
            }
        )
        
        return ExperimentResult(
            experiment_id=experiment.id,
            baseline_version=self.prompt_storage.get_version(baseline_version_id).version,
            candidate_version=self.prompt_storage.get_version(candidate_version_id).version,
            baseline_metrics=baseline_metrics,
            candidate_metrics=candidate_metrics,
            improvement_delta=improvement_delta,
            promoted=False,  # Will be set by promoter
            promotion_rationale=None
        )
    
    def _compute_metrics(self, evaluation_result) -> Dict[str, float]:
        """Compute aggregate metrics from evaluation result."""
        metrics = {}
        
        # Per-dimension scores
        for score in evaluation_result.scores:
            metrics[score.dimension.value] = score.score
        
        # Overall metrics
        metrics["aggregate"] = evaluation_result.aggregate_score
        metrics["pass_rate"] = evaluation_result.passed_cases / evaluation_result.total_cases if evaluation_result.total_cases > 0 else 0.0
        
        return metrics



