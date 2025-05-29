from django.core.management.base import BaseCommand, CommandError
from verification_tasks.models import VerificationCategory, VerificationTask
# from transformers import pipeline


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        # pipe = pipeline("feature-extraction", model="microsoft/codebert-base")  
        vt = VerificationTask.objects.first()
        print(vt.get_c_file_path().absolute().as_posix())
        # c_content = vt.read_c_file()
        # embedded_c_content = pipe(c_content)
        # print(f"Embedding C content for task {vt.id}:")
        # print(embedded_c_content)
        