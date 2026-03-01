# Generated manually for ticket workflow improvements

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_clientprofile_is_online'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketcomment',
            name='send_to',
            field=models.CharField(
                choices=[('CLIENT', 'Client'), ('EMPLOYEE', 'Assigned Employee')],
                default='CLIENT',
                help_text='Who can see this comment: Client or Assigned Employee.',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='task',
            name='project',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tasks',
                to='core.project',
            ),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='related_task',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='support_ticket',
                to='core.task',
            ),
        ),
    ]
