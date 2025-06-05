from verification_tasks.models import VerificationTask, VerificationCategory, Status
from sklearn.model_selection import train_test_split
from typing import Tuple
from pydantic import BaseModel
from benchmarks.models import Benchmark
from django.db import models
import csv


def get_train_test_data(test_size: float|None=0.2, random_state=42, shuffle=True, categories: models.Manager[VerificationCategory] = VerificationCategory.objects.all()) -> Tuple[list[int], list[int]]:    
    if test_size is None:
        return [vt.pk for vt in VerificationTask.objects.all() if vt.has_c_file()], []
    elif test_size == 1.0:
        return [], [vt.pk for vt in VerificationTask.objects.all() if vt.has_c_file()]
    else: 
        vts_train, vts_test = [], []
        for vc in categories:
            vts_c = [vt.pk for vt in VerificationTask.objects.filter(category=vc, expected_result__in=[Status.TRUE, Status.ERROR, Status.FALSE, Status.UNKNOWN]) if vt.has_c_file()]
            vts_c_train, vts_c_test = train_test_split(vts_c, test_size=test_size, random_state=random_state, shuffle=shuffle)
            vts_train.extend(vts_c_train)
            vts_test.extend(vts_c_test)

    return list(vts_train), list(vts_test)

class EvaluationStrategySummary(BaseModel):
    total_score: int = 0
    total_cpu: float = 0.0
    total_memory: float = 0.0
    verification_tasks: list[int] = []
    benchmarks: list[int] = []
    correct: int = 0

    def add_result(self, verification_task: VerificationTask, benchmark: Benchmark) -> None:
        try:
            if benchmark.raw_score is None:
                score=0
            else:
                score = int(benchmark.raw_score)
        except:
            score = 0

        self.total_score += score
        self.total_cpu += benchmark.cpu if benchmark.cpu is not None else 600
        self.total_memory += benchmark.memory if benchmark.memory is not None else 600
        self.verification_tasks.append(verification_task.pk)
        self.benchmarks.append(benchmark.pk)
        self.correct += benchmark.is_correct

    def pretty_print(self) -> None:
        print("Total Score:", self.total_score)
        print("Total CPU:", self.total_cpu)
        print("Total Memory:", self.total_memory)
        print("Verification Tasks:", len(self.verification_tasks))
        print("Benchmarks:", len(self.benchmarks))
        print("# Correct:", self.correct)

    def write_to_csv(self, filename: str) -> None:
        with open(filename, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['verification_task', 'verification_task_id', 'verifier', 'status', 'cpu', 'memory', 'status_display', 'raw_score', "is_correct"])
            for vt_id, benchmark_id in zip(self.verification_tasks, self.benchmarks):
                vt = VerificationTask.objects.get(id=vt_id)
                benchmark = Benchmark.objects.get(id=benchmark_id)
                writer.writerow([
                    vt.name,
                    vt.pk,
                    benchmark.verifier.name,
                    benchmark.status,
                    benchmark.cpu,
                    benchmark.memory,
                    benchmark.status_display,
                    benchmark.raw_score,
                    benchmark.is_correct
                ])
