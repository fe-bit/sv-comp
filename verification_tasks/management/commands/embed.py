from django.core.management.base import BaseCommand, CommandError
from verification_tasks.models import VerificationCategory, VerificationTask
from verification_tasks.embedding.embedder import embed_verifications_tasks
from verification_tasks.embedding.query import query_verification_task, query
# from transformers import pipeline


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        vts = VerificationTask.objects.all()
        embed_verifications_tasks(vts)

#         results = query_verification_task(vts[0], n_results=5)
#         print(f"Results for {vts[0].name}\n----------------------")
#         for r in results:
#             print(f"""Task: {r['verification_task'].name}
# Distance: {r['distance']}
# ----------------------""")
