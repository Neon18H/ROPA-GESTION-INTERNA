from django.db import migrations

SQL = """
ALTER TABLE purchases_purchaseorder
  ADD COLUMN IF NOT EXISTS notes text;
"""

class Migration(migrations.Migration):
    dependencies = [
        ("purchases", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop),
    ]