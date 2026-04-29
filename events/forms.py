from django import forms
from .models import Participant, Feedback, Event
from .validators import validate_receipt_file


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['student_id', 'name', 'email', 'event', 'transaction_id', 'receipt']
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. STU2024001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'event': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. TXN20241234'
            }),
            'receipt': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.png,.jpg,.jpeg'
            }),
        }
        labels = {
            'student_id': 'Student ID',
            'transaction_id': 'Transaction ID',
            'receipt': 'Payment Receipt (PDF/PNG/JPG, max 2MB)',
        }

    def clean_receipt(self):
        receipt = self.cleaned_data.get('receipt')
        if receipt:
            validate_receipt_file(receipt)
        return receipt

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        qs = Participant.objects.filter(student_id=student_id)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f"A participant with Student ID '{student_id}' is already registered."
            )
        return student_id

    def clean_transaction_id(self):
        transaction_id = self.cleaned_data.get('transaction_id')
        qs = Participant.objects.filter(transaction_id=transaction_id)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f"Transaction ID '{transaction_id}' has already been used."
            )
        return transaction_id


class FeedbackForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, '⭐' * i) for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Rating'
    )

    class Meta:
        model = Feedback
        fields = ['rating', 'comments']
        widgets = {
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience about the event...'
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                raise forms.ValidationError("Rating must be between 1 and 5.")
        except (TypeError, ValueError):
            raise forms.ValidationError("Invalid rating value.")
        return rating


class BulkUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV File',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text='CSV must contain columns: name, email, student_id, transaction_id, event_id'
    )
    
