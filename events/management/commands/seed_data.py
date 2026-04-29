"""
Management command to seed demo data for the event_cert project.
Run with: python manage.py seed_data
"""
import uuid
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from events.models import Event, Participant, Feedback


class Command(BaseCommand):
    help = 'Seed demo events and participants for development/testing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding demo data...'))

        # ── Events ────────────────────────────────────────────────────────────
        events_data = [
            {'name': 'National Tech Summit 2024', 'date': date.today() + timedelta(days=30)},
            {'name': 'AI & Machine Learning Workshop', 'date': date.today() + timedelta(days=60)},
            {'name': 'Web Development Bootcamp', 'date': date.today() - timedelta(days=10)},
        ]

        events = []
        for ed in events_data:
            event, created = Event.objects.get_or_create(
                name=ed['name'],
                defaults={'date': ed['date']}
            )
            events.append(event)
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'  {status}: Event "{event.name}"')

        # ── Participants ──────────────────────────────────────────────────────
        participants_data = [
            {
                'student_id': 'STU2024001',
                'name': 'Alice Johnson',
                'email': 'alice@example.com',
                'transaction_id': 'TXN20241001',
                'event': events[0],
                'attendance': True,
                'feedback_submitted': True,
                'transaction_verified': True,
            },
            {
                'student_id': 'STU2024002',
                'name': 'Bob Smith',
                'email': 'bob@example.com',
                'transaction_id': 'TXN20241002',
                'event': events[0],
                'attendance': True,
                'feedback_submitted': False,
                'transaction_verified': True,
            },
            {
                'student_id': 'STU2024003',
                'name': 'Carol Williams',
                'email': 'carol@example.com',
                'transaction_id': 'TXN20241003',
                'event': events[1],
                'attendance': False,
                'feedback_submitted': False,
                'transaction_verified': True,
            },
            {
                'student_id': 'STU2024004',
                'name': 'David Lee',
                'email': 'david@example.com',
                'transaction_id': 'TXN20241004',
                'event': events[2],
                'attendance': True,
                'feedback_submitted': True,
                'transaction_verified': True,
            },
            {
                'student_id': 'STU2024005',
                'name': 'Eve Martinez',
                'email': 'eve@example.com',
                'transaction_id': 'TXN20241005',
                'event': events[2],
                'attendance': True,
                'feedback_submitted': False,
                'transaction_verified': False,
            },
        ]

        created_participants = []
        for pd in participants_data:
            participant, created = Participant.objects.get_or_create(
                student_id=pd['student_id'],
                defaults={
                    'name': pd['name'],
                    'email': pd['email'],
                    'transaction_id': pd['transaction_id'],
                    'event': pd['event'],
                    'attendance': pd['attendance'],
                    'feedback_submitted': pd['feedback_submitted'],
                    'transaction_verified': pd['transaction_verified'],
                }
            )
            created_participants.append(participant)
            status = 'Created' if created else 'Already exists'
            cert_ready = '✔ cert-ready' if participant.can_get_certificate else ''
            self.stdout.write(
                f'  {status}: Participant "{participant.name}" '
                f'[{participant.student_id}] {cert_ready}'
            )

        # ── Feedback for cert-eligible participants ───────────────────────────
        for participant in created_participants:
            if participant.feedback_submitted:
                fb, created = Feedback.objects.get_or_create(
                    participant=participant,
                    defaults={'rating': 5, 'comments': 'Great event! Very informative.'}
                )
                if created:
                    self.stdout.write(
                        f'  Created: Feedback for "{participant.name}"'
                    )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Demo data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write('  Quick links (after runserver):')
        self.stdout.write('    Home        → http://127.0.0.1:8000/')
        self.stdout.write('    Register    → http://127.0.0.1:8000/register/')
        self.stdout.write('    Dashboard   → http://127.0.0.1:8000/dashboard/')
        self.stdout.write('    Stats API   → http://127.0.0.1:8000/api/stats/')
        self.stdout.write('')
        self.stdout.write('  Cert-ready participant (Alice Johnson):')
        alice = Participant.objects.filter(student_id='STU2024001').first()
        if alice:
            self.stdout.write(
                f'    Certificate → http://127.0.0.1:8000/certificate/{alice.pk}/'
            )
            self.stdout.write(
                f'    Verify      → http://127.0.0.1:8000/verify/{alice.certificate_id}/'
            )
