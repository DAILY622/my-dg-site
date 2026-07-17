# Generated migration for start_date field change
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('investments', '0004_add_payment_method_to_deposit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='investment',
            name='start_date',
            field=models.DateTimeField(default=timezone.now),
        ),
    ]
