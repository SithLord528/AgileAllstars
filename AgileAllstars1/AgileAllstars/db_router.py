class AgileDBRouter:
    """
    Routes database operations for the AgileAllstars project.

    Default database  (agile_auth.sqlite3)     – auth, sessions, admin,
                                                  and the existing taskStatus app.
    Projects database (agile_projects.sqlite3)  – sprints app (Project, Sprint,
                                                  BacklogItem).
    """

    project_app_labels = {'sprints'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.project_app_labels:
            return 'projects'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.project_app_labels:
            return 'projects'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        db1 = self._db_for(obj1)
        db2 = self._db_for(obj2)
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.project_app_labels:
            return db == 'projects'
        return db == 'default'

    # ------------------------------------------------------------------
    def _db_for(self, obj):
        if obj._meta.app_label in self.project_app_labels:
            return 'projects'
        return 'default'
