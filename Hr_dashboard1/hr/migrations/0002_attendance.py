from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('hr', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('check_in', models.TimeField(blank=True, null=True)),
                ('check_out', models.TimeField(blank=True, null=True)),
                ('total_hours', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=5)),
                ('status', models.CharField(choices=[('PRESENT', 'Present'), ('ABSENT', 'Absent'), ('LATE', 'Late')], default='PRESENT', max_length=20)),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='attendances', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Attendance records',
                'ordering': ['-date', 'user'],
                'unique_together': {('user', 'date')},
            },
        ),
    ]
