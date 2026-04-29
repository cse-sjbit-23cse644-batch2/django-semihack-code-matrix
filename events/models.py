import uuid
from django.db import models
from .validators import validate_receipt_file


class Event(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.name} ({self.date})"


class Participant(models.Model):
    student_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    transaction_id = models.CharField(max_length=100, unique=True)
    receipt = models.FileField(upload_to='receipts/')
    attendance = models.BooleanField(default=False)
    feedback_submitted = models.BooleanField(default=False)
    transaction_verified = models.BooleanField(default=True)
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.name} ({self.student_id})"

    @property
    def can_get_certificate(self):
        return (
            self.attendance is True
            and self.feedback_submitted is True
            and self.transaction_verified is True
        )


class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    participant = models.OneToOneField(
        Participant,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.participant.name} — {self.rating}/5"
