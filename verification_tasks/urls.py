from django.urls import path
from .views import verification_category_list, verification_task_detail, verification_category_detail

urlpatterns = [
    path('', verification_category_list, name='verification_task_list'),
    path('category/<int:category_id>', verification_category_detail, name='verification_category_detail'),
    path('<int:task_id>', verification_task_detail, name='verification_task_detail'),

]