from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.index, name='index'),

    # Registration
    path('register/', views.register, name='register'),

    path('toggle-transaction/<int:pk>/', views.toggle_transaction, name='toggle_transaction'),

    # Admin Dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # AJAX: Attendance Toggle
    path('toggle-attendance/<int:participant_id>/', views.toggle_attendance, name='toggle_attendance'),

    # Feedback
    path('feedback/<int:pk>/', views.feedback, name='feedback'),

    # Certificate Download
    path('certificate/<int:participant_id>/', views.download_certificate, name='download_certificate'),

    # Certificate Verification (public)
    path('verify/<uuid:certificate_id>/', views.verify_certificate, name='verify_certificate'),

    # API: Real-time stats
    path('api/stats/', views.api_stats, name='api_stats'),

    # Bulk CSV Upload
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),

    # Participant detail
    path('participant/<int:participant_id>/', views.participant_detail, name='participant_detail'),
]
