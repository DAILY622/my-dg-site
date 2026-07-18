from django.urls import path
from . import views

app_name = 'kyc'

urlpatterns = [
    path('upload/', views.upload_kyc, name='upload'),
    path('status/', views.kyc_status, name='status'),
    path('ai-verify/', views.kyc_ai_verify, name='ai_verify'),
]
