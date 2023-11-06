from django.contrib import admin
from . models import *


admin.site.register(Group)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Dependent)
admin.site.register(Reply)
admin.site.register(GroupMembership)

