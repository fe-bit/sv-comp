from django.urls import path
from .views import verifier_list, verifier_detail

urlpatterns = [
    path('', verifier_list, name='verifier_list'),
    path('<int:id>/', verifier_detail, name="verifier_detail"),
]