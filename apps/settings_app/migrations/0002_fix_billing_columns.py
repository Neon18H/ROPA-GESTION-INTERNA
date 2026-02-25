from django.db import migrations

SQL = """
ALTER TABLE settings_app_storesettings
  ADD COLUMN IF NOT EXISTS billing_legal_name varchar(160) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS billing_tax_id varchar(40) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS billing_address varchar(200) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS billing_postal_code varchar(20) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS billing_email varchar(254) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS billing_phone varchar(40) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS billing_city varchar(80) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS billing_country varchar(80) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS billing_vat_rate numeric(5,2) NOT NULL DEFAULT 0.00;
"""

class Migration(migrations.Migration):
    dependencies = [
        ("settings_app", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop),
    ]