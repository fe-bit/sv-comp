from verification_tasks.models import VerificationTask
from sklearn.model_selection import train_test_split
from typing import Tuple
from pydantic import BaseModel
from benchmarks.models import Benchmark
import csv


def get_train_test_data(n: int|None=300, test_size: float|None=0.2, random_state=42) -> Tuple[list[VerificationTask], list[VerificationTask]]:
    if n is None:
        vts = list(VerificationTask.objects.all())
    else:
        vts = list(VerificationTask.objects.all()[:n])
    
    if test_size is None:
        vts_train, vts_test = vts, []
    elif test_size == 1.0:
        vts_train, vts_test = [], vts
    else: 
        vts_train, vts_test = train_test_split(vts, test_size=test_size, random_state=random_state)

    return vts_train, vts_test

class EvaluationStrategySummary(BaseModel):
    total_score: int = 0
    total_cpu: float = 0.0
    total_memory: float = 0.0
    verification_tasks: list[int] = []
    benchmarks: list[int] = []

    def add_result(self, verification_task: VerificationTask, benchmark: Benchmark) -> None:
        self.total_score += int(benchmark.raw_score) 
        self.total_cpu += benchmark.cpu
        self.total_memory += benchmark.memory
        self.verification_tasks.append(verification_task.id)
        self.benchmarks.append(benchmark.id)

    def pretty_print(self) -> None:
        print("Total Score:", self.total_score)
        print("Total CPU:", self.total_cpu)
        print("Total Memory:", self.total_memory)
        print("Verification Tasks:", len(self.verification_tasks))
        print("Benchmarks:", len(self.benchmarks))

    def write_to_csv(self, filename: str) -> None:
        with open(filename, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['verification_task', 'verification_task_id', 'verifier', 'status', 'cpu', 'memory', 'status_display', 'raw_score', "is_correct"])
            for vt_id, benchmark_id in zip(self.verification_tasks, self.benchmarks):
                vt = VerificationTask.objects.get(id=vt_id)
                benchmark = Benchmark.objects.get(id=benchmark_id)
                writer.writerow([
                    vt.name,
                    vt.id,
                    benchmark.verifier.name,
                    benchmark.status,
                    benchmark.cpu,
                    benchmark.memory,
                    benchmark.status_display,
                    benchmark.raw_score,
                    benchmark.is_correct
                ])
