from django.apps import AppConfig
import os
import sys


class SprintsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sprints'

    def ready(self):
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return

        from django.conf import settings

        db_path = settings.DATABASES['projects']['NAME']

        try:
            if not os.path.exists(db_path):
                print(f'Projects database not found at {db_path}. Creating...')
                from django.core.management import call_command
                call_command('migrate', database='projects', verbosity=1)
                print('Projects database created successfully.')
            else:
                from django.db import connections
                conn = connections['projects']
                conn.ensure_connection()
                print(f'Projects database connection verified at {db_path}.')
        except Exception as e:
            print(f'Projects database initialization error: {e}')
            raise
