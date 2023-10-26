# Generated by Django 4.0.1 on 2023-10-24 20:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chema', '0003_remove_group_deceased'),
        ('condolence', '0005_contribution_group_admin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contribution',
            name='group_admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='groupmembership', to='chema.groupmembership'),
        ),
    ]