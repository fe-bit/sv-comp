from django.urls import path
from .views import verification_task_list, verification_task_detail

urlpatterns = [
    path('', verification_task_list, name='verification_task_list'),
    path('<int:id>', verification_task_detail, name='verification_task_detail'),

]