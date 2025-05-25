from django.urls import path
from .views import verification_task_list

urlpatterns = [
    path('', verification_task_list, name='verification_task_list'),
]