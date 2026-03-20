from django.apps import AppConfig
import os
import sys


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        from django.conf import settings

        # Avoid running during migrate/makemigrations commands
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return

        db_path = settings.DATABASES['default']['NAME']

        try:
            if not os.path.exists(db_path):
                print(f'Database not found at {db_path}. Creating...')
                from django.core.management import call_command
                call_command('migrate', verbosity=1)
                print('Database created successfully.')
            else:
                from django.db import connection
                connection.ensure_connection()
                print(f'Database connection verified at {db_path}.')
        except Exception as e:
            print(f'Database initialization error: {e}')
            raise
