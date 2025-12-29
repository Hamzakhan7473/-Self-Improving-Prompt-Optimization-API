"""Main evaluator that combines deterministic and LLM-based evaluation."""
from typing import List, Dict, Any, Optional
from datetime import datetime

from models import EvaluationDimension, EvaluationScore, EvaluationResponse
from utils.validators import ValidatorRegistry
from utils.llm_client import get_llm_client
from utils.prompt_utils import render_prompt
from evaluation.judge import LLMJudge
from evaluation.dataset import Dataset
from storage.evaluation_storage import EvaluationStorage
from storage.prompt_storage import PromptStorage


class Evaluator:
    """Main evaluator for prompts."""
    
    def __init__(
        self,
        prompt_storage: PromptStorage,
        evaluation_storage: EvaluationStorage,
        use_llm_judge: bool = True
    ):
        self.prompt_storage = prompt_storage
        self.evaluation_storage = evaluation_storage
        self.use_llm_judge = use_llm_judge
        self.judge = LLMJudge() if use_llm_judge else None
        self.llm_client = get_llm_client()
    
    def evaluate(
        self,
        prompt_version_id: int,
        dataset: Dataset,
        dimensions: Optional[List[EvaluationDimension]] = None
    ) -> EvaluationResponse:
        """
        Evaluate a prompt version on a dataset.
        
        Returns comprehensive evaluation results.
        """
        prompt_version = self.prompt_storage.get_version(prompt_version_id)
        if not prompt_version:
            raise ValueError(f"Prompt version {prompt_version_id} not found")
        
        if dimensions is None:
            dimensions = list(EvaluationDimension)
        
        # Evaluate each case
        per_case_results = []
        dimension_scores = {dim: [] for dim in dimensions}
        
        for case_idx, case in enumerate(dataset.cases):
            case_result = self._evaluate_case(
                prompt_version=prompt_version,
                case=case,
                dimensions=dimensions
            )
            per_case_results.append(case_result)
            
            # Aggregate scores by dimension
            for dim_score in case_result.get("scores", []):
                dim = dim_score["dimension"]
                if dim in dimension_scores:
                    dimension_scores[dim].append(dim_score["score"])
        
        # Compute aggregate scores
        evaluation_scores = []
        for dim in dimensions:
            scores = dimension_scores[dim]
            if scores:
                avg_score = sum(scores) / len(scores)
                evaluation_scores.append(
                    EvaluationScore(
                        dimension=dim,
                        score=avg_score,
                        details={"per_case_scores": scores}
                    )
                )
                
                # Save to storage
                self.evaluation_storage.save_result(
                    prompt_version_id=prompt_version_id,
                    dataset_id=dataset.dataset_id,
                    dimension=dim.value,
                    score=avg_score,
                    metadata={"per_case_scores": scores}
                )
        
        # Compute aggregate score (weighted average)
        aggregate_score = sum(es.score for es in evaluation_scores) / len(evaluation_scores) if evaluation_scores else 0.0
        
        # Count passed/failed cases
        passed_cases = sum(1 for r in per_case_results if r.get("passed", False))
        failed_cases = len(per_case_results) - passed_cases
        
        return EvaluationResponse(
            prompt_version_id=prompt_version_id,
            dataset_id=dataset.dataset_id,
            scores=evaluation_scores,
            aggregate_score=aggregate_score,
            total_cases=len(dataset.cases),
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            per_case_breakdown=per_case_results,
            created_at=datetime.utcnow()
        )
    
    def _evaluate_case(
        self,
        prompt_version,
        case: Dict[str, Any],
        dimensions: List[EvaluationDimension]
    ) -> Dict[str, Any]:
        """Evaluate a single test case."""
        # Render prompt
        variables = case.get("input", {})
        filled_prompt = render_prompt(prompt_version.template, variables)
        
        # Generate output
        output = self.llm_client.complete(filled_prompt)
        
        # Evaluate on each dimension
        case_scores = []
        all_passed = True
        
        for dimension in dimensions:
            score_result = self._evaluate_dimension(
                output=output,
                case=case,
                dimension=dimension,
                prompt_version=prompt_version
            )
            
            case_scores.append({
                "dimension": dimension.value,
                "score": score_result["score"],
                "details": score_result.get("details", {})
            })
            
            if score_result["score"] < 0.5:  # Threshold for "passed"
                all_passed = False
        
        return {
            "case_index": case.get("index", 0),
            "input": variables,
            "output": output,
            "scores": case_scores,
            "passed": all_passed
        }
    
    def _evaluate_dimension(
        self,
        output: str,
        case: Dict[str, Any],
        dimension: EvaluationDimension,
        prompt_version
    ) -> Dict[str, Any]:
        """Evaluate output on a specific dimension."""
        # First, try deterministic validators
        if dimension == EvaluationDimension.FORMAT_ADHERENCE:
            if prompt_version.schema_definition:
                is_valid, details = ValidatorRegistry.validate(
                    "json_schema",
                    output,
                    prompt_version.schema_definition
                )
                if is_valid:
                    return {"score": 1.0, "details": details}
                else:
                    # Partial credit for format issues
                    return {"score": 0.3, "details": details}
        
        # Use LLM judge for other dimensions or as fallback
        if self.judge:
            judgment = self.judge.evaluate(
                output=output,
                expected=case.get("expected_output"),
                rubric=case.get("rubric"),
                dimension=dimension.value,
                context=case.get("context")
            )
            return {
                "score": judgment.get("score", 0.0),
                "details": {
                    "explanation": judgment.get("explanation"),
                    "strengths": judgment.get("strengths", []),
                    "weaknesses": judgment.get("weaknesses", [])
                }
            }
        
        # Fallback: simple heuristic
        return {"score": 0.5, "details": {"method": "heuristic"}}

