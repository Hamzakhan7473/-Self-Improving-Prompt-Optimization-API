"""Failure case analyzer."""
from typing import List, Dict, Any
from collections import defaultdict

from evaluation.evaluator import Evaluator
from evaluation.dataset import Dataset


class FailureAnalyzer:
    """Analyzes failure cases to identify patterns."""
    
    def __init__(self, evaluator: Evaluator):
        self.evaluator = evaluator
    
    def analyze_failures(
        self,
        evaluation_result,
        dataset: Dataset
    ) -> Dict[str, Any]:
        """
        Analyze failure cases from evaluation.
        
        Returns patterns, common issues, and recommendations.
        """
        per_case = evaluation_result.per_case_breakdown or []
        
        # Categorize failures
        failures_by_dimension = defaultdict(list)
        failures_by_score_range = defaultdict(list)
        
        for case in per_case:
            if not case.get("passed", False):
                # Analyze which dimensions failed
                for score in case.get("scores", []):
                    if score["score"] < 0.5:
                        failures_by_dimension[score["dimension"]].append(case)
                
                # Categorize by score
                min_score = min(s["score"] for s in case.get("scores", []))
                if min_score < 0.3:
                    failures_by_score_range["critical"].append(case)
                elif min_score < 0.5:
                    failures_by_score_range["moderate"].append(case)
        
        # Identify patterns
        patterns = self._identify_patterns(per_case, failures_by_dimension)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            failures_by_dimension,
            failures_by_score_range,
            patterns
        )
        
        return {
            "total_failures": len([c for c in per_case if not c.get("passed", False)]),
            "failures_by_dimension": {
                dim: len(cases) for dim, cases in failures_by_dimension.items()
            },
            "failures_by_severity": {
                severity: len(cases) for severity, cases in failures_by_score_range.items()
            },
            "patterns": patterns,
            "recommendations": recommendations,
            "sample_failures": {
                dim: cases[:3] for dim, cases in failures_by_dimension.items()
            }
        }
    
    def _identify_patterns(
        self,
        all_cases: List[Dict[str, Any]],
        failures_by_dimension: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Identify common patterns in failures."""
        patterns = []
        
        # Pattern: Format failures
        if "format_adherence" in failures_by_dimension:
            format_failures = failures_by_dimension["format_adherence"]
            patterns.append({
                "type": "format_adherence",
                "count": len(format_failures),
                "description": "Outputs not following required format",
                "suggested_fix": "Add explicit format instructions or examples"
            })
        
        # Pattern: Low correctness scores
        if "correctness" in failures_by_dimension:
            correctness_failures = failures_by_dimension["correctness"]
            patterns.append({
                "type": "correctness",
                "count": len(correctness_failures),
                "description": "Incorrect or inaccurate outputs",
                "suggested_fix": "Improve clarity of instructions or add examples"
            })
        
        # Pattern: Verbosity issues
        if "verbosity" in failures_by_dimension:
            verbosity_failures = failures_by_dimension["verbosity"]
            patterns.append({
                "type": "verbosity",
                "count": len(verbosity_failures),
                "description": "Output length not appropriate",
                "suggested_fix": "Add explicit length constraints or examples"
            })
        
        return patterns
    
    def _generate_recommendations(
        self,
        failures_by_dimension: Dict[str, List[Dict[str, Any]]],
        failures_by_score_range: Dict[str, List[Dict[str, Any]]],
        patterns: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if "format_adherence" in failures_by_dimension:
            recommendations.append(
                "Add explicit format instructions with examples to improve format adherence"
            )
        
        if "correctness" in failures_by_dimension:
            recommendations.append(
                "Clarify instructions or add few-shot examples to improve correctness"
            )
        
        if "critical" in failures_by_score_range:
            recommendations.append(
                f"Address {len(failures_by_score_range['critical'])} critical failures first"
            )
        
        if not recommendations:
            recommendations.append("Review edge cases and add more specific instructions")
        
        return recommendations

