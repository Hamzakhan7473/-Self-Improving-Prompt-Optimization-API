"""Rubric management for evaluation."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class RubricCriterion(BaseModel):
    """Individual criterion in a rubric."""
    name: str
    description: str
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Weight for this criterion")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum score to pass")


class EvaluationRubric(BaseModel):
    """
    Structured evaluation rubric.
    
    Based on best practices from:
    - https://blog.promptlayer.com/what-are-prompt-evaluations/
    - https://www.promptingguide.ai/guides/optimizing-prompts
    """
    rubric_id: str
    name: str
    description: str
    criteria: List[RubricCriterion] = Field(
        ...,
        description="List of evaluation criteria"
    )
    dimensions: List[str] = Field(
        default=["correctness", "format_adherence", "verbosity", "safety", "consistency"],
        description="Evaluation dimensions this rubric covers"
    )
    metadata: Optional[Dict[str, Any]] = None
    
    def get_criterion(self, name: str) -> Optional[RubricCriterion]:
        """Get a criterion by name."""
        for criterion in self.criteria:
            if criterion.name == name:
                return criterion
        return None
    
    def compute_weighted_score(self, scores: Dict[str, float]) -> float:
        """Compute weighted score from dimension scores."""
        total_weight = 0.0
        weighted_sum = 0.0
        
        for criterion in self.criteria:
            if criterion.name in scores:
                weight = criterion.weight
                score = scores[criterion.name]
                weighted_sum += weight * score
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight


class RubricRegistry:
    """Registry for evaluation rubrics."""
    
    _rubrics: Dict[str, EvaluationRubric] = {}
    
    @classmethod
    def register(cls, rubric: EvaluationRubric):
        """Register a rubric."""
        cls._rubrics[rubric.rubric_id] = rubric
    
    @classmethod
    def get(cls, rubric_id: str) -> Optional[EvaluationRubric]:
        """Get a rubric by ID."""
        return cls._rubrics.get(rubric_id)
    
    @classmethod
    def list_all(cls) -> List[EvaluationRubric]:
        """List all registered rubrics."""
        return list(cls._rubrics.values())
    
    @classmethod
    def create_default_rubric(cls, task_type: str = "general") -> EvaluationRubric:
        """
        Create a default rubric based on task type.
        
        Based on best practices from prompt evaluation guides.
        """
        if task_type == "summarization":
            return EvaluationRubric(
                rubric_id=f"default_{task_type}",
                name=f"Default {task_type.title()} Rubric",
                description="Standard evaluation rubric for summarization tasks",
                criteria=[
                    RubricCriterion(
                        name="correctness",
                        description="Factual accuracy and correctness of the summary",
                        weight=0.4,
                        threshold=0.8
                    ),
                    RubricCriterion(
                        name="completeness",
                        description="All key points from the original text are included",
                        weight=0.3,
                        threshold=0.7
                    ),
                    RubricCriterion(
                        name="conciseness",
                        description="Appropriate length and verbosity",
                        weight=0.2,
                        threshold=0.7
                    ),
                    RubricCriterion(
                        name="clarity",
                        description="Clear and easy to understand",
                        weight=0.1,
                        threshold=0.7
                    )
                ],
                dimensions=["correctness", "verbosity", "consistency"]
            )
        else:
            # General purpose rubric
            return EvaluationRubric(
                rubric_id="default_general",
                name="Default General Purpose Rubric",
                description="Standard evaluation rubric for general tasks",
                criteria=[
                    RubricCriterion(
                        name="correctness",
                        description="Factual accuracy and correctness",
                        weight=0.35,
                        threshold=0.8
                    ),
                    RubricCriterion(
                        name="relevance",
                        description="Response directly addresses the prompt",
                        weight=0.25,
                        threshold=0.7
                    ),
                    RubricCriterion(
                        name="format_adherence",
                        description="Follows required format and structure",
                        weight=0.2,
                        threshold=0.8
                    ),
                    RubricCriterion(
                        name="clarity",
                        description="Clear and easy to understand",
                        weight=0.1,
                        threshold=0.7
                    ),
                    RubricCriterion(
                        name="safety",
                        description="Safe, appropriate, and free from harmful content",
                        weight=0.1,
                        threshold=0.9
                    )
                ]
            )

