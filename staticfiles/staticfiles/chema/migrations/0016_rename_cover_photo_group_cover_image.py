# Generated by Django 4.0.1 on 2023-08-25 15:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chema', '0015_group_cover_photo_delete_administrator'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='cover_photo',
            new_name='cover_image',
        ),
    ]
