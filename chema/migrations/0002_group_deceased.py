# Generated by Django 4.0.1 on 2023-10-23 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chema', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='deceased',
            field=models.BooleanField(default=False),
        ),
    ]
