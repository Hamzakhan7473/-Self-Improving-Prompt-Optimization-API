"""
Example: A/B Testing and Canary Deployment

This example demonstrates how to use the A/B testing features for
production prompt deployment, following best practices from:
- Langfuse: https://langfuse.com/docs/prompt-management/features/a-b-testing
- PromptLayer: https://blog.promptlayer.com/what-are-prompt-evaluations/
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"


def create_ab_test_versions():
    """Create baseline and candidate versions for A/B testing."""
    print("Creating prompt versions for A/B test...")
    
    # Create baseline version
    baseline = {
        "prompt_id": "summarization_ab",
        "template": "Summarize the following text: {text}",
        "metadata": {"version": "baseline"}
    }
    
    response = requests.post(f"{BASE_URL}/prompts/", json=baseline)
    baseline_version = response.json()
    print(f"Baseline version created: {baseline_version['version']} (ID: {baseline_version['id']})")
    
    # Promote baseline to active
    requests.post(f"{BASE_URL}/prompts/versions/{baseline_version['id']}/promote")
    
    # Create candidate version (improved)
    candidate = {
        "prompt_id": "summarization_ab",
        "template": "Summarize the following text in 2-3 sentences, focusing on key points: {text}",
        "metadata": {"version": "candidate", "improvement": "Added length constraint and focus instruction"},
        "parent_version": baseline_version['version']
    }
    
    response = requests.post(f"{BASE_URL}/prompts/", json=candidate)
    candidate_version = response.json()
    print(f"Candidate version created: {candidate_version['version']} (ID: {candidate_version['id']})")
    
    return baseline_version['id'], candidate_version['id']


def configure_ab_test(baseline_id: int, candidate_id: int):
    """Configure A/B test with traffic splitting."""
    print("\nConfiguring A/B test...")
    
    config = {
        "prompt_id": "summarization_ab",
        "version_a_id": baseline_id,
        "version_b_id": candidate_id,
        "traffic_split": 0.1,  # 10% traffic to candidate (canary)
        "enabled": True,
        "metadata": {
            "description": "Testing improved summarization prompt",
            "start_date": "2025-01-01"
        }
    }
    
    response = requests.post(f"{BASE_URL}/ab-testing/config", json=config)
    print(f"A/B test configured: {response.json()['config_id']}")
    return response.json()


def simulate_requests(prompt_id: str, num_requests: int = 20):
    """Simulate production requests with A/B testing."""
    print(f"\nSimulating {num_requests} production requests...")
    
    results = {
        "baseline": 0,
        "candidate": 0,
        "users": {}
    }
    
    for i in range(num_requests):
        user_id = f"user_{i % 10}"  # 10 unique users
        
        # Select version via A/B testing endpoint
        response = requests.get(
            f"{BASE_URL}/ab-testing/select/{prompt_id}",
            params={"user_id": user_id}
        )
        selection = response.json()
        
        version_type = "candidate" if selection['is_canary'] else "baseline"
        results[version_type] += 1
        
        if user_id not in results["users"]:
            results["users"][user_id] = []
        results["users"][user_id].append({
            "version": selection['selected_version'],
            "is_canary": selection['is_canary']
        })
        
        # Simulate request delay
        time.sleep(0.1)
    
    print(f"\nTraffic distribution:")
    print(f"  Baseline: {results['baseline']} requests ({results['baseline']/num_requests*100:.1f}%)")
    print(f"  Candidate: {results['candidate']} requests ({results['candidate']/num_requests*100:.1f}%)")
    
    # Show consistent assignment (same user gets same version)
    print(f"\nConsistent user assignment:")
    for user_id, assignments in list(results["users"].items())[:3]:
        versions = [a['version'] for a in assignments]
        print(f"  {user_id}: {set(versions)} (consistent: {len(set(versions)) == 1})")
    
    return results


def check_metrics(prompt_id: str):
    """Check A/B test metrics."""
    print(f"\nChecking A/B test metrics for {prompt_id}...")
    
    response = requests.get(f"{BASE_URL}/ab-testing/metrics/{prompt_id}")
    metrics = response.json()
    
    print(f"\nVersion Metrics:")
    for metric in metrics['metrics']:
        status_indicator = "✓" if metric['is_active'] else " "
        print(f"  {status_indicator} v{metric['version']} ({metric['status']}): "
              f"score={metric['aggregate_score']:.3f}")
    
    return metrics


def main():
    """Main A/B testing workflow."""
    print("=" * 60)
    print("A/B Testing & Canary Deployment Example")
    print("=" * 60)
    
    try:
        # Step 1: Create versions
        baseline_id, candidate_id = create_ab_test_versions()
        
        # Step 2: Configure A/B test
        config = configure_ab_test(baseline_id, candidate_id)
        
        # Step 3: Simulate production traffic
        traffic_results = simulate_requests("summarization_ab", num_requests=20)
        
        # Step 4: Check metrics
        metrics = check_metrics("summarization_ab")
        
        print("\n" + "=" * 60)
        print("A/B Testing Example Completed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Monitor metrics over time")
        print("2. Gradually increase traffic split if candidate performs well")
        print("3. Promote candidate to active if metrics meet thresholds")
        print("4. Rollback if metrics degrade")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()



