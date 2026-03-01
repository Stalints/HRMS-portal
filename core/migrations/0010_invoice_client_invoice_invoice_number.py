import django.db.models.deletion
from django.db import migrations, models

def fill_invoice_numbers(apps, schema_editor):
    Invoice = apps.get_model("core", "Invoice")
    
    # Fill only missing/blank ones
    qs = Invoice.objects.filter(
        models.Q(invoice_number__isnull=True) | models.Q(invoice_number="")
    ).order_by("id")

    for inv in qs:
        inv.invoice_number = f"INV-{inv.id:06d}"
        inv.save(update_fields=["invoice_number"])

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_invoice_tax_1_name_invoice_tax_1_percentage_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='client',
            field=models.ForeignKey(
                blank=True, 
                null=True, 
                on_delete=django.db.models.deletion.CASCADE, 
                related_name='invoices_direct', 
                to='core.clientprofile',
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='invoice_number',
            field=models.CharField(
                max_length=50, 
                unique=True, 
                null=True,
                blank=True,
            ),
        ),
        migrations.RunPython(fill_invoice_numbers, migrations.RunPython.noop),
    ]