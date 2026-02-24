from django.db import migrations

SQL = """
ALTER TABLE inventory_stock
  ADD COLUMN IF NOT EXISTS last_cost numeric(12,2),
  ADD COLUMN IF NOT EXISTS avg_cost numeric(12,2);
"""

class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop),
    ]
