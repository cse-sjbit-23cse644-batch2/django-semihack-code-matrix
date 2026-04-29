import json
import os
from urllib import response
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from .models import Event, Participant, Feedback
from .forms import ParticipantForm, FeedbackForm, BulkUploadForm
from .utils import (
    generate_certificate,
    send_registration_email,
    process_bulk_csv,
)


# ─────────────────────────────────────────────────────────────────────────────
# HOME / INDEX
# ─────────────────────────────────────────────────────────────────────────────

def index(request):
    """Landing page with links to registration and dashboard."""
    events = Event.objects.all()
    total_participants = Participant.objects.count()
    return render(request, 'events/index.html', {
        'events': events,
        'total_participants': total_participants,
    })


# ─────────────────────────────────────────────────────────────────────────────
# EVENT REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────

def register(request):
    """Handle participant registration with full validation."""
    form = ParticipantForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            participant = form.save()
            # Send confirmation email (printed to console)
            send_registration_email(participant)
            messages.success(
                request,
                f"🎉 Registration successful! Welcome, {participant.name}. "
                f"A confirmation has been sent to {participant.email}."
            )
            return redirect('register')
        else:
            messages.error(request, "Please fix the errors below and resubmit.")

    return render(request, 'events/register.html', {'form': form})
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Participant

@require_POST
def toggle_transaction(request, pk):
    participant = Participant.objects.get(pk=pk)

    # Toggle True/False
    participant.transaction_verified = not participant.transaction_verified
    participant.save()

    return JsonResponse({
        "transaction_verified": participant.transaction_verified
    })

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def admin_dashboard(request):
    """Admin view: list all participants with attendance toggle and stats."""
    event_id = request.GET.get('event')
    events = Event.objects.all()

    participants = Participant.objects.select_related('event').all()
    if event_id:
        participants = participants.filter(event_id=event_id)

    # Stats
    total = participants.count()
    attended = participants.filter(attendance=True).count()
    certified = sum(1 for p in participants if p.can_get_certificate)

    bulk_form = BulkUploadForm()

    return render(request, 'events/admin_dashboard.html', {
        'participants': participants,
        'events': events,
        'selected_event': event_id,
        'total': total,
        'attended': attended,
        'certified': certified,
        'bulk_form': bulk_form,
    })


# ─────────────────────────────────────────────────────────────────────────────
# AJAX: ATTENDANCE TOGGLE
# ─────────────────────────────────────────────────────────────────────────────

@require_POST
def toggle_attendance(request, participant_id):
    """AJAX endpoint to toggle attendance. Returns JSON."""
    try:
        participant = get_object_or_404(Participant, pk=participant_id)
        participant.attendance = not participant.attendance
        participant.save(update_fields=['attendance'])

        return JsonResponse({
            'success': True,
            'attendance': participant.attendance,
            'participant_id': participant_id,
            'message': (
                f"Attendance marked for {participant.name}"
                if participant.attendance
                else f"Attendance removed for {participant.name}"
            ),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



# ─────────────────────────────────────────────────────────────────────────────
# CERTIFICATE DOWNLOAD
# ─────────────────────────────────────────────────────────────────────────────

def download_certificate(request, participant_id):
  
    participant = get_object_or_404(Participant, pk=participant_id)

    if not participant.can_get_certificate:
        missing = []
        if not participant.attendance:
            missing.append("Attendance not marked")
        if not participant.feedback_submitted:
            missing.append("Feedback not submitted")
        if not participant.transaction_verified:
            missing.append("Transaction not verified")

        return render(
            request,
            'events/certificate_denied.html',
            {'participant': participant, 'missing': missing},
            status=403,
        )

    # Build the verification URL
    verify_url = request.build_absolute_uri(
        f'/verify/{participant.certificate_id}/'
    )

    import os

    file_path = generate_certificate(participant)

    if not os.path.exists(file_path):
        raise Http404("Certificate not found")

    with open(file_path, 'rb') as f:
       response = HttpResponse(f.read(), content_type='application/pdf')

    response['Content-Disposition'] = (
        f'attachment; filename="certificate_{participant.student_id}.pdf"'
)

    return response


# ─────────────────────────────────────────────────────────────────────────────
# CERTIFICATE VERIFICATION PAGE
# ─────────────────────────────────────────────────────────────────────────────

def verify_certificate(request, certificate_id):
    """Public verification page for a certificate."""
    try:
        participant = get_object_or_404(Participant, certificate_id=certificate_id)
        verified = participant.can_get_certificate
    except Exception:
        participant = None
        verified = False

    return render(request, 'events/verify.html', {
        'participant': participant,
        'verified': verified,
        'certificate_id': certificate_id,
    })


# ─────────────────────────────────────────────────────────────────────────────
# API: REAL-TIME STATS (AJAX POLLING)
# ─────────────────────────────────────────────────────────────────────────────

@require_GET
def api_stats(request):
    """JSON endpoint for real-time dashboard statistics."""
    event_id = request.GET.get('event')

    qs = Participant.objects.all()
    if event_id:
        qs = qs.filter(event_id=event_id)

    total = qs.count()
    attended = qs.filter(attendance=True).count()
    feedback_done = qs.filter(feedback_submitted=True).count()
    verified = qs.filter(transaction_verified=True).count()

    # Certified = all three conditions True
    certified = qs.filter(
        attendance=True,
        feedback_submitted=True,
        transaction_verified=True
    ).count()

    return JsonResponse({
        'total': total,
        'attended': attended,
        'feedback_done': feedback_done,
        'verified': verified,
        'certified': certified,
    })


# ─────────────────────────────────────────────────────────────────────────────
# BULK CSV UPLOAD
# ─────────────────────────────────────────────────────────────────────────────

@require_POST
def bulk_upload(request):
    """Admin feature: bulk-create participants from a CSV file."""
    form = BulkUploadForm(request.POST, request.FILES)

    if form.is_valid():
        csv_file = request.FILES['csv_file']
        created_count, errors = process_bulk_csv(csv_file)

        if created_count > 0:
            messages.success(
                request,
                f"✅ Successfully imported {created_count} participant(s)."
            )
        if errors:
            for err in errors:
                messages.warning(request, err)
        if created_count == 0 and not errors:
            messages.info(request, "No new participants were imported.")
    else:
        messages.error(request, "Please upload a valid CSV file.")

    return redirect('admin_dashboard')


# ─────────────────────────────────────────────────────────────────────────────
# PARTICIPANT DETAIL (helper for feedback link from dashboard)
# ─────────────────────────────────────────────────────────────────────────────

def participant_detail(request, participant_id):
    """Simple detail page for a participant."""
    participant = get_object_or_404(Participant, pk=participant_id)
    return render(request, 'events/participant_detail.html', {
        'participant': participant,
    })
from django.shortcuts import render, get_object_or_404, redirect
from .models import Participant
from .forms import FeedbackForm

def feedback(request, pk):
    participant = get_object_or_404(Participant, pk=pk)

    # Prevent duplicate feedback
    if participant.feedback_submitted:
        return render(request, "events/feedback.html", {
            "participant": participant,
            "already_submitted": True
        })

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            participant.feedback_submitted = True
            participant.save()

            return redirect("certificate", pk=participant.pk)

    else:
        form = FeedbackForm()

    return render(request, "events/feedback.html", {
        "form": form,
        "participant": participant
    })