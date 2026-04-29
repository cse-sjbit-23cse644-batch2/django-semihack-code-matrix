from django.contrib import admin
from .models import Event, Participant, Feedback


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'date']
    search_fields = ['name']


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'student_id', 'email', 'event',
        'attendance', 'feedback_submitted', 'transaction_verified',
        'registered_at'
    ]
    list_filter = ['attendance', 'feedback_submitted', 'transaction_verified', 'event']
    search_fields = ['name', 'student_id', 'email', 'transaction_id']
    readonly_fields = ['certificate_id', 'registered_at']
    list_editable = ['attendance', 'transaction_verified']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['participant', 'rating', 'submitted_at']
    list_filter = ['rating']
    search_fields = ['participant__name']
