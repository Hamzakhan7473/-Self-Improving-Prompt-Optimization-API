"""
Example usage of the Self-Improving Prompt Optimization API.

This script demonstrates:
1. Creating a prompt version
2. Running inference
3. Evaluating the prompt
4. Running self-improvement
"""

import json
import requests
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def create_prompt():
    """Create a new prompt version."""
    print("Creating prompt...")
    
    prompt_data = {
        "prompt_id": "summarization_v1",
        "template": "Summarize the following text in 2-3 sentences: {text}",
        "schema_definition": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "maxLength": 500}
            },
            "required": ["summary"]
        },
        "metadata": {
            "task": "summarization",
            "domain": "general"
        }
    }
    
    response = requests.post(f"{BASE_URL}/prompts/", json=prompt_data)
    response.raise_for_status()
    version = response.json()
    print(f"Created prompt version: {version['version']} (ID: {version['id']})")
    return version


def run_inference(prompt_id: str, text: str):
    """Run inference with a prompt."""
    print(f"\nRunning inference with prompt {prompt_id}...")
    
    request_data = {
        "prompt_id": prompt_id,
        "variables": {
            "text": text
        }
    }
    
    response = requests.post(f"{BASE_URL}/inference/", json=request_data)
    response.raise_for_status()
    result = response.json()
    print(f"Output: {result['output'][:200]}...")
    return result


def load_dataset():
    """Load sample dataset."""
    dataset_path = Path(__file__).parent / "sample_dataset.json"
    with open(dataset_path) as f:
        return json.load(f)


def evaluate_prompt(version_id: int, dataset: dict):
    """Evaluate a prompt version."""
    print(f"\nEvaluating prompt version {version_id}...")
    
    request_data = {
        "request": {
            "prompt_version_id": version_id,
            "dataset_id": dataset["dataset_id"]
        },
        "dataset_data": dataset
    }
    
    response = requests.post(f"{BASE_URL}/evaluation/", json=request_data)
    response.raise_for_status()
    result = response.json()
    
    print(f"Aggregate score: {result['aggregate_score']:.3f}")
    print(f"Passed cases: {result['passed_cases']}/{result['total_cases']}")
    for score in result['scores']:
        print(f"  {score['dimension']}: {score['score']:.3f}")
    
    return result


def run_self_improvement(version_id: int, dataset: dict):
    """Run self-improvement loop."""
    print(f"\nRunning self-improvement for version {version_id}...")
    
    request_data = {
        "dataset_data": dataset,
        "auto_promote": False
    }
    
    response = requests.post(
        f"{BASE_URL}/improvement/self-improve/{version_id}",
        json=request_data
    )
    response.raise_for_status()
    result = response.json()
    
    print(f"Generated {result['candidates_generated']} candidates")
    print(f"Ran {len(result['experiments'])} experiments")
    
    if result['promoted_version_id']:
        print(f"Promoted version: {result['promoted_version_id']}")
    else:
        print("No version was auto-promoted")
    
    return result


def main():
    """Main example flow."""
    print("=" * 60)
    print("Self-Improving Prompt Optimization API - Example Usage")
    print("=" * 60)
    
    try:
        # Step 1: Create prompt
        version = create_prompt()
        version_id = version['id']
        prompt_id = version['prompt_id']
        
        # Step 2: Run inference
        sample_text = "Artificial intelligence has revolutionized many industries..."
        run_inference(prompt_id, sample_text)
        
        # Step 3: Load dataset
        dataset = load_dataset()
        
        # Step 4: Evaluate prompt
        evaluation_result = evaluate_prompt(version_id, dataset)
        
        # Step 5: Run self-improvement (optional, can be slow)
        # Uncomment to run:
        # improvement_result = run_self_improvement(version_id, dataset)
        
        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()


