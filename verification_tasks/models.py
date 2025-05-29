from django.db import models
from pathlib import Path
import yaml

import re

def clean_i_file_for_pycparser(code: str) -> str:
    # Remove __attribute__((...))
    code = re.sub(r'__attribute__\s*\(\(.*?\)\)', '', code)
    
    # Remove __extension__ and similar GNU extensions
    code = re.sub(r'__extension__', '', code)
    
    # Optionally: Remove inline functions, compiler hints, etc.
    return code


class VerificationCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Status(models.TextChoices):
    TRUE = "true", "True"
    FALSE = "false", "False"
    INVALID_TASK = "invalid_task", "Invalid Task"
    UNKNOWN = "unknown", "Unknown"
    ERROR = "error", "Error"

class VerificationTask(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(VerificationCategory, on_delete=models.CASCADE)
    expected_result = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.TRUE,
        help_text="Expected result for the task."
    )

    class Meta:
        ordering = ['category', "name"]

    def __str__(self):
        return self.name
    
    @property
    def yml_file_path(self) -> Path:
        return Path("sv-benchmarks/c") / self.name[:self.name.find("yml")+3]
    
    def get_yml_config(self):
        try:
            with open(self.yml_file_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            return None
        
    def get_c_file_path(self) -> Path:
        return self.yml_file_path.parent / Path(self.get_yml_config().get("input_files")).with_stem(".c")
    
    def get_i_file_path(self) -> Path:
        return self.yml_file_path.parent / Path(self.get_yml_config().get("input_files")).with_stem(".i")

    def read_c_file(self) -> str | None:
        c_file_path = self.get_c_file_path()
        if c_file_path.exists():
            with open(c_file_path, 'r') as file:
                return file.read()
        return None
    
    def read_i_file(self) -> str | None:
        c_file_path = self.get_c_file_path()
        if c_file_path.exists():
            with open(c_file_path, 'r') as file:
                return clean_i_file_for_pycparser(file.read())
        return None
    
    