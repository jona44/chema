# Generated by Django 4.0.1 on 2023-10-23 13:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chema', '0002_group_deceased'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='deceased',
        ),
    ]