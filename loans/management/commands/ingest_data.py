"""
Management command to trigger data ingestion via Celery background tasks.

Usage:
    python manage.py ingest_data
    python manage.py ingest_data --sync   (run without Celery, for debugging)
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Trigger background ingestion of customer_data.xlsx and loan_data.xlsx'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run ingestion synchronously (without Celery)',
        )

    def handle(self, *args, **options):
        from loans.tasks import ingest_customer_data, ingest_loan_data

        if options['sync']:
            self.stdout.write('Running ingestion synchronously...')
            result1 = ingest_customer_data()
            self.stdout.write(self.style.SUCCESS(f'  {result1}'))
            result2 = ingest_loan_data()
            self.stdout.write(self.style.SUCCESS(f'  {result2}'))
        else:
            self.stdout.write('Dispatching ingestion tasks to Celery...')
            task1 = ingest_customer_data.delay()
            self.stdout.write(self.style.SUCCESS(
                f'  Customer ingestion task dispatched: {task1.id}'
            ))
            task2 = ingest_loan_data.delay()
            self.stdout.write(self.style.SUCCESS(
                f'  Loan ingestion task dispatched: {task2.id}'
            ))

        self.stdout.write(self.style.SUCCESS('Done.'))
