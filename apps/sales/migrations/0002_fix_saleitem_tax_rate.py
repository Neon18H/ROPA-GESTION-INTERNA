from django.db import migrations

SQL = """
ALTER TABLE sales_saleitem
  ADD COLUMN IF NOT EXISTS tax_rate numeric(5,2) NOT NULL DEFAULT 0.00,
  ADD COLUMN IF NOT EXISTS discount numeric(12,2) NOT NULL DEFAULT 0.00,
  ADD COLUMN IF NOT EXISTS line_total numeric(12,2) NOT NULL DEFAULT 0.00;
"""

class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop),
    ]