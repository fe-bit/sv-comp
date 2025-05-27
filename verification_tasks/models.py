from django.db import models

class VerificationCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class VerificationTask(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(VerificationCategory, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
