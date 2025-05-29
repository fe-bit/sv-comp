import os

# https://sv-comp.sosy-lab.org/2025/results/results-verified/

urls = [
    "https://sv-comp.sosy-lab.org/2025/results/results-verified/META_MemSafety.table.html#/table",
    "https://sv-comp.sosy-lab.org/2025/results/results-verified/META_ReachSafety.table.html#/table",
    "https://sv-comp.sosy-lab.org/2025/results/results-verified/META_ConcurrencySafety.table.html#/table",
]

def get_file(url: str, output_dir: str) -> str:
    return os.path.join(output_dir, url.split("/")[-2].replace(".html#", "") + ".json")

from pydantic import BaseModel, PrivateAttr, computed_field
import os
from typing import List, Optional


class Verifier(BaseModel):
    name: str

    _verifier_name: str = PrivateAttr(default_factory=str)
    _test_date: str = PrivateAttr(default_factory=str)
    _verification_specs: list[str] = PrivateAttr(default_factory=list)

    def load_data(self) -> str:
        idx = self.name.find("[")
        prefix = self.name[:idx]
        self._verification_specs = self.name[idx+1:-1].split("; ")
        self._verifier_name = prefix[:prefix.find("2024")].strip()
        self._test_date = prefix[prefix.find("2024"):prefix.find("CET ")+3].strip()

    @computed_field
    @property
    def verifier_name(self) -> str:
        if self._verifier_name == "":
            self.load_data()
        return self._verifier_name
    
    @computed_field
    @property
    def test_date(self) -> str:
        if self._test_date == "":
            self.load_data()
        return self._test_date
    
    @computed_field
    @property
    def verification_specs(self) -> list[str]:
        if len(self._verification_specs) == 0:
            self.load_data()
        return self._verification_specs

class VerificationTask(BaseModel):
    name: str

class VerifierResult(BaseModel):
    verification_task: VerificationTask
    verifier: Verifier
    status: str
    raw_core: Optional[str]
    cpu: Optional[float]
    memory: Optional[float]

class VerificationResults(BaseModel):
    verification_results: list[VerifierResult] = []

    _verifiers_cache: List["Verifier"] = PrivateAttr(default_factory=list)
    _verification_tasks_cache: List["VerificationTask"] = PrivateAttr(default_factory=list)

    def extend(self, other:"VerificationResults") -> None:
        self.verification_results.extend(other.verification_results)
        
        self._verifiers_cache = []
        self._verification_tasks_cache = []

    @property
    def verifiers(self) -> list[Verifier]:
        if not self._verifiers_cache:
            verifiers_names = set()
            verifiers = []
            for vr in self.verification_results:
                name = vr.verifier.name
                if name not in verifiers_names:
                    verifiers.append(vr.verifier)
                    verifiers_names.add(name)
            self._verifiers_cache = verifiers
            self._verifiers_cached_names = verifiers_names
        return self._verifiers_cache
    
    @property
    def verification_tasks(self) -> list[VerificationTask]:
        if not self._verification_tasks_cache:
            verification_task_names = set()
            verification_tasks = []
            for vr in self.verification_results:
                name = vr.verification_task.name
                if name not in verification_task_names:
                    verification_tasks.append(vr.verification_task)
                    verification_task_names.add(name)
            self._verification_tasks_cache = verification_tasks
        return self._verification_tasks_cache
    
    def summary(self, indent=0) -> str:
        text = indent * "    " + f"Verification Tasks: {len(self.verification_tasks)}\n"
        text += indent * "    " + f"Verifiers: {len(self.verifiers)}\n"
        text += indent * "    " + f"Verification Results: {len(self.verification_results)}"
        return text
    
from collections import defaultdict


def get_verification_results(url, output_dir="tables") -> VerificationResults:
    file_name = get_file(url, output_dir)
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            data = f.read()
        return VerificationResults.model_validate_json(data)
    else:
        print(f"File {file_name} does not exist.")
        return None
    
class SVCOMP:
    def __init__(self):
        from .sv_comp_scraper import save_all_pages
        for url in urls:
            save_all_pages(url, "tables", overwrite=False)
        
        self.data: dict[str, VerificationResults] = {
            "mem_safety": get_verification_results(urls[0]),
            "reach_safety": get_verification_results(urls[1]),
            "concurrency_safety": get_verification_results(urls[2])
        }

    def summary(self) -> str:
        return f"""SV-COMP25:
MemSafety: 
{self.data["mem_safety"].summary(indent=1)}
ReachSafety: 
{self.data["reach_safety"].summary(indent=1)}
ConcurrencySafety: 
{self.data["concurrency_safety"].summary(indent=1)}
"""
    
    def get_training_data(self) -> dict:
        grouped_by_verifier = defaultdict(list)

        for result in self.data["mem_safety"].verification_results:
            key = result.verifier.verifier_name
            grouped_by_verifier[key].append(result)
        
        for result in self.data["reach_safety"].verification_results:
            key = result.verifier.verifier_name
            grouped_by_verifier[key].append(result)

        for result in self.data["concurrency_safety"].verification_results:
            key = result.verifier.verifier_name
            grouped_by_verifier[key].append(result)

        return dict(grouped_by_verifier)
    

def get_svcomp() -> SVCOMP:
    return SVCOMP()