# Generated by Django 4.0.1 on 2023-10-24 12:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('condolence', '0002_remove_contribution_status_remove_contribution_user_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contribution',
            old_name='deceased',
            new_name='deceased_group',
        ),
    ]