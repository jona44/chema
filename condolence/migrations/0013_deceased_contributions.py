# Generated by Django 4.0.1 on 2023-11-19 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('condolence', '0012_alter_deceased_deceased'),
    ]

    operations = [
        migrations.AddField(
            model_name='deceased',
            name='contributions',
            field=models.BooleanField(default=True),
        ),
    ]
