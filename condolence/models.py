# models.py in the condolences app
from django.db import models
from django.contrib.auth.models import User
from django.apps import apps
from chema.models import *
from user.models import Profile


class Contribution(models.Model):
    group           = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_contributions')
    deceased_member = models.ForeignKey('Deceased', on_delete=models.CASCADE, related_name='member_deceased', null=True, blank=True)
    contributing_member = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='deceased_contributions', null=True, blank=True)
    group_admin = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='admin_contributions', null=True, blank=True)
    amount      = models.DecimalField(default=100.00, max_digits=10, decimal_places=2)
    contribution_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Contribution by {self.contributing_member} on {self.contribution_date} in {self.group.name} for{self.deceased_member}"
    
    class Meta:
        unique_together = ('deceased_member', 'contributing_member')
    
class Deceased(models.Model):
    deceased  = models.OneToOneField(Profile, on_delete=models.CASCADE,related_name='profile_deceased',default=True, unique=True)
    group     = models.ForeignKey(Group, on_delete=models.CASCADE)
    date      = models.DateField(auto_now_add=True)
    group_admin = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin')
    contributions_open = models.BooleanField(default=True)
    cont_is_active = models.BooleanField(default=True)

    def __str__ (self):
       return f"{self.deceased}"
   
    def stop_contributions(self):
        self.cont_is_active = False
        self.save()