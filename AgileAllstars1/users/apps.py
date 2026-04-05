from django.apps import AppConfig
import os
import sys


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        from django.conf import settings

        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return

        db_path = settings.DATABASES['default']['NAME']
        old_db_path = db_path.parent / 'db.sqlite3'

        try:
            if not os.path.exists(db_path):
                if os.path.exists(old_db_path):
                    os.rename(old_db_path, db_path)
                    print(f'Renamed {old_db_path.name} -> {db_path.name}')
                else:
                    print(f'Auth database not found at {db_path}. Creating...')
                    from django.core.management import call_command
                    call_command('migrate', verbosity=1)
                    print('Auth database created successfully.')

            from django.db import connection
            connection.ensure_connection()
            print(f'Auth database connection verified at {db_path}.')
        except Exception as e:
            print(f'Auth database initialization error: {e}')
            raise
