"""
Management command for database backup
"""
import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Backup the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Directory to store backups'
        )
    
    def handle(self, *args, **options):
        output_dir = options['output_dir']
        
        # Create backup directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(output_dir, f'db_backup_{timestamp}.sqlite3')
        
        # Get database path from settings
        db_path = settings.DATABASES['default']['NAME']
        
        # Copy database file
        try:
            if str(db_path).endswith('.sqlite3'):
                # For SQLite, simply copy the file
                import shutil
                shutil.copy2(db_path, backup_file)
                self.stdout.write(self.style.SUCCESS(f'Database backed up to: {backup_file}'))
            else:
                # For PostgreSQL or other databases
                self.stdout.write(self.style.WARNING('Please configure backup for your database type'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Backup failed: {str(e)}'))
