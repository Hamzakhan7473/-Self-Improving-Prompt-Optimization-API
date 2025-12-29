"""Data models for prompt optimization system."""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class PromptStatus(str, Enum):
    """Status of a prompt version."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class EvaluationDimension(str, Enum):
    """Evaluation dimensions."""
    CORRECTNESS = "correctness"
    FORMAT_ADHERENCE = "format_adherence"
    VERBOSITY = "verbosity"
    SAFETY = "safety"
    CONSISTENCY = "consistency"


class EvaluationResult(Base):
    """Database model for evaluation results."""
    __tablename__ = "evaluation_results"
    
    id = Column(Integer, primary_key=True)
    prompt_version_id = Column(Integer, ForeignKey("prompt_versions.id"))
    dataset_id = Column(String, nullable=False)
    dimension = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    prompt_version = relationship("PromptVersion", back_populates="evaluation_results")


class PromptVersion(Base):
    """Database model for prompt versions."""
    __tablename__ = "prompt_versions"
    
    id = Column(Integer, primary_key=True)
    prompt_id = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    template = Column(Text, nullable=False)
    schema_definition = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    parent_version_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=True)
    status = Column(String, default=PromptStatus.DRAFT.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    promoted_at = Column(DateTime, nullable=True)
    
    evaluation_results = relationship("EvaluationResult", back_populates="prompt_version")
    parent = relationship("PromptVersion", remote_side=[id])


class Experiment(Base):
    """Database model for A/B experiments."""
    __tablename__ = "experiments"
    
    id = Column(Integer, primary_key=True)
    baseline_version_id = Column(Integer, ForeignKey("prompt_versions.id"))
    candidate_version_id = Column(Integer, ForeignKey("prompt_versions.id"))
    dataset_id = Column(String, nullable=False)
    metrics = Column(JSON, nullable=False)
    improvement_rationale = Column(Text, nullable=True)
    promoted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic models for API


class PromptTemplate(BaseModel):
    """Prompt template with schema."""
    prompt_id: str = Field(..., description="Unique identifier for the prompt")
    template: str = Field(..., description="Prompt template with {variable} placeholders")
    schema_definition: Optional[Dict[str, Any]] = Field(None, description="JSON schema for expected output")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    parent_version: Optional[str] = Field(None, description="Parent version ID for lineage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_id": "summarization_v1",
                "template": "Summarize the following text: {text}",
                "schema_definition": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "maxLength": 200}
                    },
                    "required": ["summary"]
                },
                "metadata": {"task": "summarization", "domain": "general"}
            }
        }


class PromptVersionResponse(BaseModel):
    """Response model for prompt version."""
    id: int
    prompt_id: str
    version: str
    template: str
    schema_definition: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    parent_version_id: Optional[int]
    status: str
    created_at: datetime
    promoted_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


class EvaluationRequest(BaseModel):
    """Request model for evaluation."""
    prompt_version_id: int
    dataset_id: str
    dimensions: Optional[List[EvaluationDimension]] = Field(
        None, 
        description="Specific dimensions to evaluate. If None, evaluates all."
    )


class EvaluationScore(BaseModel):
    """Individual evaluation score."""
    dimension: EvaluationDimension
    score: float = Field(..., ge=0.0, le=1.0)
    details: Optional[Dict[str, Any]] = None


class EvaluationResponse(BaseModel):
    """Response model for evaluation."""
    prompt_version_id: int
    dataset_id: str
    scores: List[EvaluationScore]
    aggregate_score: float
    total_cases: int
    passed_cases: int
    failed_cases: int
    per_case_breakdown: Optional[List[Dict[str, Any]]] = None
    created_at: datetime


class InferenceRequest(BaseModel):
    """Request model for prompt inference."""
    prompt_id: str
    variables: Dict[str, Any] = Field(..., description="Variables to fill in the prompt template")
    version: Optional[str] = Field(None, description="Specific version. If None, uses active version.")


class InferenceResponse(BaseModel):
    """Response model for prompt inference."""
    prompt_id: str
    version: str
    input_variables: Dict[str, Any]
    filled_prompt: str
    output: str
    metadata: Optional[Dict[str, Any]] = None


class ImprovementCandidate(BaseModel):
    """Candidate prompt improvement."""
    prompt_id: str
    parent_version: str
    new_template: str
    rationale: str
    expected_improvements: Optional[Dict[str, float]] = None


class ExperimentResult(BaseModel):
    """Result of an A/B experiment."""
    experiment_id: int
    baseline_version: str
    candidate_version: str
    baseline_metrics: Dict[str, float]
    candidate_metrics: Dict[str, float]
    improvement_delta: Dict[str, float]
    promoted: bool
    promotion_rationale: Optional[str] = None


class PromptDiff(BaseModel):
    """Diff between two prompt versions."""
    from_version: str
    to_version: str
    template_diff: str
    schema_diff: Optional[Dict[str, Any]] = None
    metadata_diff: Optional[Dict[str, Any]] = None


class ChangelogEntry(BaseModel):
    """Changelog entry for prompt version."""
    version: str
    timestamp: datetime
    changes: Dict[str, Any]
    rationale: Optional[str] = None
    metrics_delta: Optional[Dict[str, float]] = None

