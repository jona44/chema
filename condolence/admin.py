from django.contrib import admin
from . models import Contribution,Deceased

admin.site.register(Deceased)
admin.site.register(Contribution)
