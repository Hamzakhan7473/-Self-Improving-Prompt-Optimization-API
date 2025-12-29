"""API endpoints for prompt inference."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import InferenceRequest, InferenceResponse
from storage import get_db, PromptStorage
from utils.prompt_utils import render_prompt, validate_variables
from utils.llm_client import get_llm_client

router = APIRouter(prefix="/inference", tags=["inference"])


@router.post("/", response_model=InferenceResponse)
def run_inference(
    request: InferenceRequest,
    db: Session = Depends(get_db)
):
    """Run inference with a prompt."""
    storage = PromptStorage(db)
    
    # Get prompt version
    if request.version:
        prompt_version = storage.get_version_by_prompt_and_version(
            request.prompt_id,
            request.version
        )
    else:
        prompt_version = storage.get_active_version(request.prompt_id)
    
    if not prompt_version:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt version not found for {request.prompt_id}"
        )
    
    # Validate variables
    is_valid, missing = validate_variables(prompt_version.template, request.variables)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required variables: {', '.join(missing)}"
        )
    
    # Render prompt
    filled_prompt = render_prompt(prompt_version.template, request.variables)
    
    # Generate output
    llm_client = get_llm_client()
    output = llm_client.complete(filled_prompt)
    
    # Validate output against schema if present
    metadata = {}
    if prompt_version.schema_definition:
        from utils.validators import ValidatorRegistry
        is_valid, details = ValidatorRegistry.validate(
            "json_schema",
            output,
            prompt_version.schema_definition
        )
        metadata["schema_valid"] = is_valid
        if not is_valid:
            metadata["schema_errors"] = details
    
    return InferenceResponse(
        prompt_id=request.prompt_id,
        version=prompt_version.version,
        input_variables=request.variables,
        filled_prompt=filled_prompt,
        output=output,
        metadata=metadata
    )

