# Generated by Django 4.0.1 on 2023-11-19 20:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('condolence', '0013_deceased_contributions'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deceased',
            old_name='contributions',
            new_name='contributions_open',
        ),
    ]