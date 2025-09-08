# customuser/models.py
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)  # Superusers should be active by default

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username    = models.CharField(max_length=30, blank=True)
    email       = models.EmailField(unique=True)
    is_staff    = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=False)  # Activated after email verification
    date_joined = models.DateTimeField(default=timezone.now)

    # Email verification field
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'customuser_customuser'
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Profile(models.Model):
    user = models.OneToOneField( settings.AUTH_USER_MODEL,  on_delete=models.CASCADE, related_name="profile" ) 
    first_name    = models.CharField(max_length=255, blank=True)
    surname       = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    contact_number  = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True)
    bio             = models.TextField(blank=True)
    is_complete     = models.BooleanField(default=False)
    # Additional useful fields
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"
    
    @property
    def full_name(self):
        if self.first_name and self.surname:
            return f"{self.first_name} {self.surname}"
        return self.first_name or self.surname or self.user.email
    
    def check_completion(self):
        """Check if profile has minimum required fields filled"""
        required_fields = [self.first_name, self.surname]
        self.is_complete = all(field.strip() for field in required_fields if field)
        return self.is_complete

    class Meta:
        db_table = 'customuser_profile'


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)



