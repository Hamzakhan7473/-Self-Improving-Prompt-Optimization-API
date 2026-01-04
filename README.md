# Self-Improving Prompt Optimization API

A production-ready system for versioned prompt management with automated evaluation and self-improvement capabilities. This API provides "CI/CD for prompts" suitable for production LLM systems.

> **Research-Based**: This system implements best practices from [LangChain's prompt optimization research](https://blog.langchain.com/exploring-prompt-optimization/), [Prompting Guide](https://www.promptingguide.ai/guides/optimizing-prompts), and industry leaders. See [RESEARCH_REFERENCES.md](RESEARCH_REFERENCES.md) for details.

## Architecture

![System Architecture](Self-Improving%20Prompt%20Optimization%20API%20—%20Clean%203-Layer%20Architecture.jpg)

The system follows a clean 3-layer architecture:
- **Layer 1 - API Endpoints**: FastAPI routers for prompts, inference, evaluation, improvement, and A/B testing
- **Layer 2 - Core Services**: Storage layer, evaluation pipeline, and self-improvement loop
- **Layer 3 - External Services**: LLM providers (OpenAI, Anthropic) and database (SQLite/PostgreSQL)

## Features

### 🎯 Core Capabilities

- **Versioned Prompt Management**: Store prompts as templates with schemas, metadata, and full lineage tracking
- **Automated Evaluation**: Multi-dimensional evaluation using deterministic validators and LLM-based judges
- **Self-Improvement Loop**: Automated failure analysis, candidate generation, A/B testing, and conditional promotion
- **Transparency & Control**: Prompt diffs, changelogs, metric deltas, and natural-language explanations

### 🔍 Evaluation Dimensions

- **Correctness**: Factual accuracy and correctness
- **Format Adherence**: Compliance with required output format
- **Verbosity**: Appropriate length and detail level
- **Safety**: Harmful content detection
- **Consistency**: Consistency across similar inputs

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "Self-Improving Prompt Optimization API"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

4. Initialize the database:
```bash
python -c "from storage import init_db; init_db()"
```

5. Run the API:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Quick Start

### 1. Create a Prompt

```bash
curl -X POST "http://localhost:8000/prompts/" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_id": "summarization_v1",
    "template": "Summarize the following text in 2-3 sentences: {text}",
    "schema_definition": {
      "type": "object",
      "properties": {
        "summary": {"type": "string", "maxLength": 500}
      },
      "required": ["summary"]
    },
    "metadata": {"task": "summarization", "domain": "general"}
  }'
```

### 2. Run Inference

```bash
curl -X POST "http://localhost:8000/inference/" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_id": "summarization_v1",
    "variables": {
      "text": "Your text to summarize here..."
    }
  }'
```

### 3. Evaluate a Prompt

```bash
curl -X POST "http://localhost:8000/evaluation/" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "prompt_version_id": 1,
      "dataset_id": "test_dataset"
    },
    "dataset_data": {
      "dataset_id": "test_dataset",
      "cases": [
        {
          "input": {"text": "Sample text to summarize"},
          "expected_output": "A concise summary",
          "rubric": "Should be 2-3 sentences"
        }
      ]
    }
  }'
```

### 4. Run Self-Improvement

```bash
curl -X POST "http://localhost:8000/improvement/self-improve/1" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_data": {
      "dataset_id": "test_dataset",
      "cases": [...]
    },
    "auto_promote": false
  }'
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Architecture

### Components

1. **Storage Layer** (`storage/`)
   - Database models and operations
   - Prompt versioning and lineage
   - Evaluation result storage
   - Experiment tracking

2. **Evaluation Pipeline** (`evaluation/`)
   - Dataset management
   - Deterministic validators (JSON schema, regex, constraints)
   - LLM-based judges (blinded evaluation)
   - Multi-dimensional scoring

3. **Self-Improvement Loop** (`improvement/`)
   - Failure analysis
   - Candidate generation
   - A/B experiment runner
   - Promotion logic with guardrails

4. **API Layer** (`api/`)
   - Prompt management endpoints
   - Inference endpoints
   - Evaluation endpoints
   - Self-improvement endpoints

5. **Utilities** (`utils/`)
   - LLM client (OpenAI, Anthropic)
   - Validators
   - Prompt rendering
   - Diff computation

## Configuration

Key configuration options in `.env`:

- **LLM Providers**: Configure OpenAI and/or Anthropic API keys
- **Evaluation Settings**: Control evaluation model and temperature
- **Promotion Guardrails**:
  - `MIN_IMPROVEMENT_THRESHOLD`: Minimum improvement to promote (default: 0.05)
  - `MIN_ABSOLUTE_SCORE`: Minimum absolute score required (default: 0.7)
  - `REGRESSION_THRESHOLD`: Maximum allowed regression (default: 0.02)
  - `FORMAT_PASS_RATE`: Required format pass rate (default: 0.98)

## Evaluation Leakage Prevention

The system implements several measures to prevent evaluation leakage, critical for reliable optimization:

1. **Blinded Judges**: LLM judges are blinded to prompt version identity (see [LangChain's research](https://blog.langchain.com/exploring-prompt-optimization/))
2. **Separate Roles**: Generation and evaluation use separate LLM instances to prevent bias
3. **Deterministic Validators**: Use schema/regex validators where possible for objective evaluation
4. **Low-Variance Evaluation**: Evaluation models use temperature=0.0 for consistent scoring

### Importance of Verifiable Outcomes

As highlighted in [LangChain's prompt optimization research](https://blog.langchain.com/exploring-prompt-optimization/), optimization works best with **verifiable outcomes**:

- Clear, measurable success criteria
- Objective evaluation metrics
- Ground truth labels where possible
- Programmatically checkable constraints

Optimizing against fuzzy or unreliable metrics often makes prompts worse, not better. The system emphasizes deterministic validators and clear evaluation criteria.

## Self-Improvement Process

The system implements a comprehensive self-improvement loop based on research from [LangChain's prompt optimization study](https://blog.langchain.com/exploring-prompt-optimization/) and industry best practices:

1. **Evaluate**: Run current prompt version on dataset with verifiable outcomes
2. **Analyze**: Identify failure patterns and common issues using failure analysis
3. **Generate**: Create candidate improvements using meta-prompting techniques
4. **Experiment**: Run A/B tests comparing candidates to baseline
5. **Promote**: Conditionally promote based on guardrails and improvement thresholds

### Optimization Techniques

The system uses multiple optimization approaches:

- **Meta-Prompting**: LLM-driven prompt improvement based on failure analysis and evaluation results
- **Failure-Driven Optimization**: Targeted improvements based on specific failure cases
- **A/B Testing**: Systematic comparison of candidate prompts against baseline
- **Evolutionary Approach**: Multiple candidate generation with selection of best performers

### When Prompt Optimization Works Best

Based on research, prompt optimization is most effective when:

- **Models lack domain knowledge**: Optimization can show ~200% increase in accuracy
- **Clear patterns exist**: Rules, preferences, or conditional logic that can be learned
- **Verifiable outcomes**: Evaluation metrics are clear and measurable
- **Structured tasks**: Tasks with well-defined success criteria

For tasks where the model already has strong domain knowledge, few-shot prompting may be more effective than instruction tuning alone.

## Dataset Format

Datasets should be provided as JSON:

```json
{
  "dataset_id": "my_dataset",
  "metadata": {
    "description": "Dataset description"
  },
  "cases": [
    {
      "index": 0,
      "input": {
        "variable1": "value1",
        "variable2": "value2"
      },
      "expected_output": "Expected output text",
      "rubric": "Evaluation criteria",
      "context": {"additional": "context"},
      "metadata": {
        "critical": true
      }
    }
  ]
}
```

## A/B Testing & Canary Deployment

The system supports production A/B testing and canary deployments, following best practices from [Langfuse's A/B testing guide](https://langfuse.com/docs/prompt-management/features/a-b-testing):

### Traffic Splitting

```bash
# Select version for A/B test (with consistent user assignment)
curl "http://localhost:8000/ab-testing/select/summarization_v1?user_id=user123"
```

The system implements:
- **Consistent hashing**: Same user always gets same version (for consistent UX)
- **Traffic splitting**: Configurable percentage for canary deployment
- **Real-time metrics**: Track latency, cost, token usage per version

### Canary Deployment Workflow

1. Create experimental version
2. Configure A/B test with small traffic percentage (e.g., 10%)
3. Monitor metrics via `/ab-testing/metrics/{prompt_id}`
4. Gradually increase traffic or promote if metrics are positive

## Best Practices

Based on industry best practices from [PromptLayer](https://blog.promptlayer.com/what-are-prompt-evaluations/), [Langfuse](https://langfuse.com/docs/prompt-management/features/a-b-testing), and [Prompting Guide](https://www.promptingguide.ai/guides/optimizing-prompts):

### 1. Define Clear Goals
Before evaluating, clearly define what success looks like:
- What should the AI accomplish?
- Should it be more creative or factual?
- More detailed or concise?

### 2. Develop Structured Rubrics
Use structured rubrics with weighted criteria:
- **Relevance**: Does the response address the prompt?
- **Clarity**: Is it easy to understand?
- **Consistency**: Do similar prompts produce similar outputs?
- **Accuracy**: Are facts presented correctly?

### 3. Version Control
- Always create new versions rather than modifying existing ones
- Maintain full lineage for auditability
- Use semantic versioning for clarity

### 4. Evaluation Strategy
- **Test Cases**: Include edge cases, average cases, and stress tests
- **Train/Test Split**: Maintain separate datasets to prevent overfitting
- **Iterative Refinement**: Regularly revisit and refine based on results

### 5. Production Deployment
- **Guardrails**: Configure appropriate thresholds for your use case
- **Canary Deployment**: Start with small traffic percentage
- **Monitoring**: Regularly review evaluation results and promotion decisions
- **Rollback**: Keep deprecated versions for quick rollback if needed

### 6. Prompt Optimization Techniques
Leverage advanced techniques:
- **Few-shot prompting**: Provide examples in the prompt
- **Chain-of-thought**: Encourage step-by-step reasoning
- **Task decomposition**: Break complex tasks into smaller parts
- **Structured formatting**: Use clear structure and constraints

## Evaluation Rubrics

The system supports structured evaluation rubrics with weighted criteria. Create custom rubrics or use default templates:

```python
from evaluation.rubric import RubricRegistry, EvaluationRubric, RubricCriterion

# Create custom rubric
rubric = EvaluationRubric(
    rubric_id="my_custom_rubric",
    name="Custom Evaluation Rubric",
    description="Rubric for my specific use case",
    criteria=[
        RubricCriterion(
            name="correctness",
            description="Factual accuracy",
            weight=0.4,
            threshold=0.8
        ),
        RubricCriterion(
            name="relevance",
            description="Addresses the prompt",
            weight=0.3,
            threshold=0.7
        ),
        # ... more criteria
    ]
)

RubricRegistry.register(rubric)
```

## References & Best Practices

This implementation follows best practices from leading prompt engineering resources:

- **[PromptLayer: What Are Prompt Evaluations?](https://blog.promptlayer.com/what-are-prompt-evaluations/)** - Evaluation methodology and rubric development
- **[Langfuse: A/B Testing](https://langfuse.com/docs/prompt-management/features/a-b-testing)** - Production A/B testing and canary deployment
- **[Prompting Guide: Optimizing Prompts](https://www.promptingguide.ai/guides/optimizing-prompts)** - Advanced prompting techniques and best practices

## Limitations & Future Improvements

- Current implementation uses SQLite by default (can be upgraded to PostgreSQL)
- Caching is configured but not fully implemented
- Some evaluation metrics could be more sophisticated
- Batch evaluation could be optimized for large datasets
- Real-time metrics tracking (latency, cost) for A/B tests could be enhanced with Redis/streaming

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

