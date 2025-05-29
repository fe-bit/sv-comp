from django.core.management.base import BaseCommand, CommandError
from verification_tasks.models import VerificationCategory, VerificationTask
from pycparser import c_parser



class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        vt = VerificationTask.objects.first()
        c_file = vt.get_c_file_path()
        print(f"Parsing C file: {c_file}")
        parser = c_parser.CParser()
        ast = parser.parse(vt.read_c_file())
        print(f"AST for {c_file}:")
        print(ast)