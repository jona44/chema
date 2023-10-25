# models.py in the condolences app
from django.db import models
from django.contrib.auth.models import User
from django.apps import apps
from chema.models import *
from user.models import Profile


class Contribution(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_contributions')
    deceased_member = models.ManyToManyField(Profile, related_name='member_deceased')
    contributing_member = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='deceased_contributions', null=True, blank=True)
    group_admin = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='admin_contributions', null=True, blank=True)
    amount = models.DecimalField(default=100.00, max_digits=10, decimal_places=2)
    contribution_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Contribution by {self.contributing_member} on {self.contribution_date} in {self.group.name} for{self.deceased_member}"
