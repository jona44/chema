# Generated by Django 4.0.1 on 2023-10-23 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_remove_profile_deceased'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='deceased',
            field=models.BooleanField(default=False),
        ),
    ]
