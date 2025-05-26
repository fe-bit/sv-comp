from django.shortcuts import render
from .models import Verifier

def verifier_list(request):
    verifiers = Verifier.objects.all()
    return render(request, 'verifiers/verifier_list.html', {'verifiers': verifiers})
