# Generated by Django 4.0.1 on 2023-11-10 13:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_profile_deceased'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='deceased',
        ),
    ]
