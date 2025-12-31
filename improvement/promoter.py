"""Promotes prompt versions based on experiment results."""
from typing import Optional, Dict
from config import settings
from storage.prompt_storage import PromptStorage
from storage.experiment_storage import ExperimentStorage
from storage.evaluation_storage import EvaluationStorage
from evaluation.dataset import Dataset
from models import ExperimentResult
from utils.llm_client import get_llm_client
from utils.audit import get_audit_logger, AuditEventType


class PromptPromoter:
    """Decides whether to promote a prompt version."""
    
    def __init__(
        self,
        prompt_storage: PromptStorage,
        experiment_storage: ExperimentStorage,
        evaluation_storage: EvaluationStorage
    ):
        self.prompt_storage = prompt_storage
        self.experiment_storage = experiment_storage
        self.evaluation_storage = evaluation_storage
        self.llm_client = get_llm_client()
        self.audit_logger = get_audit_logger()
    
    def should_promote(
        self,
        experiment_result: ExperimentResult,
        dataset: Optional[Dataset] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if candidate should be promoted.
        
        Returns (should_promote, rationale)
        """
        # Check guardrails
        checks = self._run_guardrails(experiment_result, dataset)
        
        if not checks["all_passed"]:
            return False, checks["rationale"]
        
        # Generate promotion rationale
        rationale = self._generate_promotion_rationale(experiment_result, checks)
        
        return True, rationale
    
    def _run_guardrails(
        self,
        experiment_result: ExperimentResult,
        dataset: Optional[Dataset] = None
    ) -> Dict:
        """Run promotion guardrails."""
        issues = []
        
        # Check minimum improvement threshold
        aggregate_delta = experiment_result.improvement_delta.get("aggregate", 0.0)
        if aggregate_delta < settings.min_improvement_threshold:
            self.audit_logger.log_guardrail_failure(
                version_id=experiment_result.experiment_id,
                guardrail_name="min_improvement_threshold",
                reason=f"Aggregate improvement below threshold",
                threshold=settings.min_improvement_threshold,
                actual_value=aggregate_delta
            )
            issues.append(
                f"Aggregate improvement ({aggregate_delta:.3f}) below threshold "
                f"({settings.min_improvement_threshold})"
            )
        
        # Check minimum absolute score
        candidate_aggregate = experiment_result.candidate_metrics.get("aggregate", 0.0)
        if candidate_aggregate < settings.min_absolute_score:
            issues.append(
                f"Candidate absolute score ({candidate_aggregate:.3f}) below minimum "
                f"({settings.min_absolute_score})"
            )
        
        # Check for regressions
        for dim, delta in experiment_result.improvement_delta.items():
            if dim != "aggregate" and delta < -settings.regression_threshold:
                baseline_score = experiment_result.baseline_metrics.get(dim, 0.0)
                candidate_score = experiment_result.candidate_metrics.get(dim, 0.0)
                
                # Log regression for auditability
                self.audit_logger.log_regression(
                    version_id=experiment_result.experiment_id,
                    dimension=dim,
                    baseline_score=baseline_score,
                    candidate_score=candidate_score,
                    delta=delta
                )
                
                issues.append(
                    f"Regression in {dim}: {delta:.3f} (threshold: -{settings.regression_threshold})"
                )
        
        # Check format pass rate
        format_pass_rate = experiment_result.candidate_metrics.get("format_adherence", 0.0)
        if format_pass_rate < settings.format_pass_rate:
            issues.append(
                f"Format pass rate ({format_pass_rate:.3f}) below threshold "
                f"({settings.format_pass_rate})"
            )
        
        # Check critical cases
        if dataset:
            critical_cases = dataset.get_critical_cases()
        else:
            critical_cases = []
        
        if critical_cases:
            # Re-evaluate critical cases (simplified check)
            # In production, you'd want to actually re-run evaluation
            candidate_pass_rate = experiment_result.candidate_metrics.get("pass_rate", 0.0)
            if candidate_pass_rate < settings.critical_case_pass_rate:
                issues.append(
                    f"Pass rate ({candidate_pass_rate:.3f}) below critical threshold "
                    f"({settings.critical_case_pass_rate})"
                )
        
        all_passed = len(issues) == 0
        rationale = "; ".join(issues) if issues else "All guardrails passed"
        
        return {
            "all_passed": all_passed,
            "issues": issues,
            "rationale": rationale
        }
    
    def _generate_promotion_rationale(
        self,
        experiment_result: ExperimentResult,
        checks: Dict
    ) -> str:
        """Generate natural language explanation for promotion."""
        prompt = f"""Based on the following experiment results, generate a clear explanation of why this prompt version should be promoted:

Baseline metrics: {experiment_result.baseline_metrics}
Candidate metrics: {experiment_result.candidate_metrics}
Improvement deltas: {experiment_result.improvement_delta}
Guardrail checks: {checks['rationale']}

Provide a concise, natural language explanation suitable for a changelog."""
        
        response = self.llm_client.complete(
            prompt=prompt,
            system_prompt="You are a technical writer explaining prompt improvements.",
            temperature=0.3
        )
        
        return response.strip()
    
    def promote(
        self,
        experiment_id: int,
        candidate_version_id: int,
        rationale: Optional[str] = None
    ) -> None:
        """Promote a candidate version with audit logging."""
        experiment = self.experiment_storage.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        baseline_version = self.prompt_storage.get_version(experiment.baseline_version_id)
        candidate_version = self.prompt_storage.get_version(candidate_version_id)
        
        # Get metrics delta for audit trail
        metrics_delta = experiment.metrics.get("delta", {})
        
        # Log promotion with interpretable details
        change_summary = rationale or f"Promoted based on experiment {experiment_id}"
        self.audit_logger.log_prompt_change(
            from_version_id=experiment.baseline_version_id,
            to_version_id=candidate_version_id,
            change_summary=change_summary,
            metrics_delta=metrics_delta
        )
        
        # Mark experiment as promoted
        self.experiment_storage.mark_promoted(experiment_id)
        
        # Promote the version
        self.prompt_storage.promote_version(candidate_version_id)

