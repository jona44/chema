# Generated by Django 4.0.1 on 2023-11-14 08:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_remove_profile_deceased'),
        ('condolence', '0010_remove_contribution_deceased_member_deceased_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deceased',
            name='group_admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admin', to='user.profile'),
        ),
    ]
