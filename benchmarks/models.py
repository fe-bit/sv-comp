from django.db import models
from verification_tasks.models import VerificationTask, Status
from verifiers.models import Verifier
from enum import Enum

def status_from_string(status_str: str) -> Status:
    status_str = status_str.lower()
    if "true" in status_str:
        return Status.TRUE
    elif "false" in status_str:
        return Status.FALSE
    elif "invalid" in status_str:
        return Status.INVALID_TASK
    else:
        return Status.UNKNOWN

class BenchmarkManager(models.Manager):
    def correct(self):
        return self.filter(is_correct=True).order_by("cpu", "memory")


class Benchmark(models.Model):
    verification_task = models.ForeignKey(VerificationTask, on_delete=models.CASCADE)
    verifier = models.ForeignKey(Verifier, on_delete=models.CASCADE)
    # run_name = models.CharField(max_length=255, blank=True, null=True)
    test_date = models.DateTimeField()
    
    status = models.CharField(max_length=50)
    raw_score = models.IntegerField() # -64 refers to blank entry that is worse than false one
    cpu = models.FloatField(blank=True, null=True)  # CPU time in seconds
    memory = models.FloatField(blank=True, null=True)  # Memory usage in MB
  
    is_correct = models.BooleanField(default=False, help_text="Indicates if the verification result is correct based on the expected result of the task.")
    status_display = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.ERROR,
        help_text="Status of the benchmark."
    )
    objects = BenchmarkManager()

    class Meta:
        ordering = ['verifier', "verification_task"]

    def __str__(self):
        return f"{self.verification_task} - {self.verifier} - {self.test_date.strftime('%d/%m/%Y, %H:%M:%S')}"
