from django.db import models
from verification_tasks.models import VerificationTask
from verifiers.models import Verifier


class VerificationSpecification(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Benchmark(models.Model):
    verification_task = models.ForeignKey(VerificationTask, on_delete=models.CASCADE)
    verifier = models.ForeignKey(Verifier, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=50)
    raw_core = models.TextField(blank=True, null=True)  # Raw core dump or output from the verifier
    cpu = models.FloatField(blank=True, null=True)  # CPU time in seconds
    memory = models.FloatField(blank=True, null=True)  # Memory usage in MB

    test_date = models.DateTimeField()
    verification_specs = models.ManyToManyField(VerificationSpecification, blank=True)

    def __str__(self):
        return f"{self.verification_task} - {self.verifier} - {self.status}"