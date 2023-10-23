from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.core.files import File
from io import BytesIO


# Create your models here.
class Profile(models.Model):
   
    user        = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(default='default.jpg', upload_to='profile_pics')
    bio         = models.TextField()
    phone       = models.CharField(max_length=10,null=True,blank=True)
    address     = models.TextField(null=True,blank=True)
    first_name  = models.CharField(max_length=20)
    surname     = models.CharField(max_length=20)
    deceased    = models.BooleanField(default=False)
 
    
    def __str__(self):
        return f'{self.user.username}' 

    def resize_profile_photo(self):
        if not self.profile_pic:
            return

        # Open the original image using Pillow
        img = Image.open(self.profile_pic)

        # Resize the image to 300x300
        target_size = (300, 300)
        img.thumbnail(target_size, Image.ANTIALIAS)

        # Save the resized image to a BytesIO buffer
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=90)

        # Update the ImageField with the resized image
        self.profile_pic.save(self.profile_pic.name, File(buffer), save=False)