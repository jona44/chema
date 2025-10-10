import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse

# Create your models here.
class Memorial(models.Model):
    """Memorial page for the deceased - central hub for remembrance"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Deceased Information
    deceased = models.ForeignKey('customuser.Profile', blank=True, null=True, on_delete=models.CASCADE, related_name='memorials')
    
    # Memorial Details
    photo = models.ImageField(upload_to='memorials/', blank=True, null=True)
    biography = models.TextField(help_text="Tell their story, achievements, and impact")
    location_of_death = models.CharField(max_length=200, blank=True)
    burial_location = models.CharField(max_length=200, blank=True)
    
    
    # Funeral Details
    funeral_date = models.DateTimeField(blank=True, null=True)
    funeral_venue = models.CharField(max_length=300, blank=True)
    funeral_details = models.TextField(blank=True, help_text="Service details, dress code, etc.")
    
    # Platform Management
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_memorials')
    family_admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='administered_memorials', blank=True)
    associated_group = models.ForeignKey('group.Group', on_delete=models.CASCADE, related_name='memorial')
    
    # Settings
    is_public = models.BooleanField(default=False, help_text="Can non-group members view?")
    allow_condolences = models.BooleanField(default=True)
    allow_memories = models.BooleanField(default=True)
    allow_photos   = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Memorial for {self.deceased.full_name}" # type: ignore

    

    def get_absolute_url(self):
        return reverse('memorial_detail', kwargs={'pk': self.pk})

    

    def is_admin(self, user):
        return user == self.created_by or user in self.family_admins.all()
