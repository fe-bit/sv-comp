from django.shortcuts import render
from .models import VerificationTask

def verification_task_list(request):
    tasks = VerificationTask.objects.all()
    return render(request, 'verification_tasks/verificationtask_list.html', {'tasks': tasks})
