# Generated by Django 4.2.1 on 2023-08-07 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chema', '0008_remove_post_approved'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='approved',
            field=models.BooleanField(default=False),
        ),
    ]
