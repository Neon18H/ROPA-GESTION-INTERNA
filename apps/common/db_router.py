class SettingsRouter:
    """Routes settings_app models to the MySQL settings_db database."""

    settings_app_label = 'settings_app'
    settings_db_alias = 'settings_db'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.settings_app_label:
            return self.settings_db_alias
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.settings_app_label:
            return self.settings_db_alias
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == self.settings_db_alias:
            return app_label == self.settings_app_label
        if db == 'default' and app_label == self.settings_app_label:
            return False
        return None
