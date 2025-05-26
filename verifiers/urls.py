from django.urls import path
from .views import verifier_list

urlpatterns = [
    path('', verifier_list, name='verifier_list'),
]