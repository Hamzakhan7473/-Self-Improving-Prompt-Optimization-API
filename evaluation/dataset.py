"""Dataset management for evaluation."""
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import yaml


class Dataset:
    """Evaluation dataset."""
    
    def __init__(
        self,
        dataset_id: str,
        cases: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.dataset_id = dataset_id
        self.cases = cases
        self.metadata = metadata or {}
    
    def __len__(self):
        return len(self.cases)
    
    def __getitem__(self, idx):
        return self.cases[idx]
    
    def get_case(self, idx: int) -> Dict[str, Any]:
        """Get a specific test case."""
        return self.cases[idx]
    
    def get_critical_cases(self) -> List[Dict[str, Any]]:
        """Get critical test cases (marked as critical)."""
        return [
            case for case in self.cases
            if case.get("metadata", {}).get("critical", False)
        ]


class DatasetLoader:
    """Loader for evaluation datasets."""
    
    @staticmethod
    def load_from_file(file_path: str) -> Dataset:
        """Load dataset from JSON or YAML file."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        with open(path, 'r') as f:
            if path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        dataset_id = data.get("dataset_id", path.stem)
        cases = data.get("cases", [])
        metadata = data.get("metadata", {})
        
        return Dataset(dataset_id=dataset_id, cases=cases, metadata=metadata)
    
    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> Dataset:
        """Load dataset from dictionary."""
        dataset_id = data.get("dataset_id", "unknown")
        cases = data.get("cases", [])
        metadata = data.get("metadata", {})
        
        return Dataset(dataset_id=dataset_id, cases=cases, metadata=metadata)
    
    @staticmethod
    def create_from_cases(
        dataset_id: str,
        cases: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dataset:
        """Create dataset from list of cases."""
        return Dataset(dataset_id=dataset_id, cases=cases, metadata=metadata)



