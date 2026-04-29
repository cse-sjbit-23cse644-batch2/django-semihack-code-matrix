from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import qrcode
import os
from django.conf import settings

from django.core.mail import send_mail

def send_registration_email(participant):
    subject = "Event Registration Successful"

    message = f"""
Hello {participant.name},

You have successfully registered for:

Event: {participant.event.name}
Date: {participant.event.date}

Your Certificate ID: {participant.certificate_id}

Thank you for participating!

- EventCert Team
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [participant.email],
        fail_silently=True
    )

import csv
from io import TextIOWrapper
from .models import Participant, Event

def process_bulk_csv(file):
    csv_file = TextIOWrapper(file.file, encoding='utf-8')
    reader = csv.DictReader(csv_file)

    created_count = 0

    for row in reader:
        try:
            event = Event.objects.get(name=row['event'])

            # Avoid duplicates
            if Participant.objects.filter(student_id=row['student_id']).exists():
                continue

            Participant.objects.create(
                name=row['name'],
                email=row['email'],
                student_id=row['student_id'],
                event=event,
                transaction_id=row['transaction_id'],
                transaction_verified=True
            )

            created_count += 1

        except Exception as e:
            print("Error:", e)
            continue

    return created_count


def generate_certificate(participant):
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    import qrcode, os
    from django.conf import settings

    file_path = os.path.join(settings.MEDIA_ROOT, f"certificate_{participant.certificate_id}.pdf")

    c = canvas.Canvas(file_path, pagesize=landscape(A4))
    width, height = landscape(A4)

    # ===== BORDER =====
    c.setStrokeColor(colors.darkblue)
    c.setLineWidth(4)
    c.rect(30, 30, width - 60, height - 60)

    # ===== HEADER =====
    c.setFillColor(colors.darkblue)
    c.rect(30, height - 110, width - 60, 60, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 80, "CERTIFICATE OF PARTICIPATION")

    # ===== CONTENT (SAFE ZONE) =====
    top = height - 150
    bottom_limit = 250   # NOTHING crosses this

    y = top

    def draw_center(text, size=12, bold=False, color=colors.black):
        nonlocal y
        if y < bottom_limit:
            return  # stop drawing to avoid overlap
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.setFillColor(color)
        c.drawCentredString(width/2, y, text)

    # Line 1
    draw_center("This is to certify that", 14)
    y -= 45

    # Name
    draw_center(participant.name, 28, True, colors.darkblue)
    y -= 40

    # Text
    draw_center("has successfully participated in", 14)
    y -= 40

    # Event
    draw_center(participant.event.name, 18, True, colors.darkblue)
    y -= 35

    # Date
    date = participant.event.date.strftime("%d-%m-%y")
    draw_center(f"Held on {date}", 12)
    y -= 30

    # Location
    draw_center("Conducted at SJB Institute of Technology", 12)
    y -= 40

    # Achievement
    draw_center(
        "Successfully completed all requirements including attendance and feedback submission",
        11
    )

    # ===== DETAILS (FIXED POSITION, NOT COLLIDING) =====
    details_y = 200

    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)

    c.drawString(120, details_y, f"Student ID: {participant.student_id}")
    c.drawString(120, details_y - 25, "Mode: Offline")
    c.drawString(120, details_y - 50, "Status: Verified")

    # ===== SIGNATURE (CLEAR SPACE) =====
    sign_y = 95

    c.line(120, sign_y, 300, sign_y)
    line_center_x = (120 + 320) / 2 + 15

    c.setFont("Helvetica-Bold", 11)
    c.drawString(120, sign_y - 20, "Authorised Signatory")

    # ===== QR CODE =====
    verify_url = f"http://127.0.0.1:8001/verify/{participant.certificate_id}/"

    qr = qrcode.make(verify_url)
    qr_path = os.path.join(settings.MEDIA_ROOT, f"qr_{participant.certificate_id}.png")
    qr.save(qr_path)

# QR position
    qr_x = width - 160
    qr_y = 130

# Draw QR
    c.drawImage(qr_path, qr_x, qr_y, width=80, height=80)

# Center text under QR and move slightly UP
    c.setFont("Helvetica", 8)

    qr_center_x = qr_x + 40   # center of QR
    text_y = qr_y - 5         # move closer to QR (upward)

    c.drawCentredString(qr_center_x, text_y, "Scan to verify")

    # ===== FOOTER (NO OVERLAP FIXED) =====
    footer_y = 50   # LOWER → more space from content

    c.setFont("Helvetica", 8)  # smaller font avoids crowding

# LEFT
    cert_id = str(participant.certificate_id)
    c.drawString(100, footer_y, f"Certificate ID: {cert_id}")  # shorten if too long
    

# CENTER
    c.drawCentredString(
    width / 2,
    footer_y,
    f"Student ID: {participant.student_id}"
)

# RIGHT (IMPORTANT: SHORTEN URL)
    short_url = f"/verify/{participant.certificate_id}/"

    c.drawRightString(
    width - 100,
    footer_y,
    f"Verify at: {short_url}"
)

    # ===== SAVE =====
    c.save()

    return file_path