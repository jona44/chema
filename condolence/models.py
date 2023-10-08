# models.py in the condolences app
from django.db import models
from django.contrib.auth.models import User
from django.apps import apps
from chema.models import Group


class Deceased(models.Model):
    name = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Add more fields for the deceased person if needed

    def __str__(self):
        return self.name

class Contribution(models.Model):
    Status =(('open','open'),('closed','closed'))
  
    group        = models.ForeignKey(Group, on_delete=models.CASCADE)
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    deceased     = models.ForeignKey(Deceased, on_delete=models.CASCADE)
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    contribution_date = models.DateField(auto_now_add=True)
    status            = models.CharField(max_length=20, blank=True, null=True,choices=(Status))
    

    def __str__(self):
        return f"Contribution by {self.user.username} on {self.contribution_date} for {self.deceased.name} in {self.group.name}"



