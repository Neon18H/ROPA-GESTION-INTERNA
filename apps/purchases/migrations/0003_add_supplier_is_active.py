from django.db import migrations

SQL = """
ALTER TABLE purchases_supplier
  ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;
"""

class Migration(migrations.Migration):
    dependencies = [
        ("purchases", "0002_add_purchaseorder_notes"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop),
    ]