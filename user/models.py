from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.core.files import File
from io import BytesIO
import uuid

from django.forms import ValidationError

def profile_picture_path(instance, filename):
    # Generate a unique filename for the profile picture
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"profile_pics/{filename}"

def validate_image(image):
    # Validate that the uploaded file is an image
    if image.file.content_type not in ['image/jpeg', 'image/png']:
        raise ValidationError("Only JPEG or PNG images are allowed.")

class Profile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(default='default.jpg', upload_to=profile_picture_path, validators=[validate_image])
    bio         = models.TextField()
    phone       = models.CharField(max_length=10, null=True, blank=True)
    address     = models.TextField()
    first_name  = models.CharField(max_length=20)
    surname     = models.CharField(max_length=20)
    
    def __str__(self):
        return f'{self.user.username}' 

    def resize_profile_photo(self):
        if not self.profile_pic:
            return

        img = Image.open(self.profile_pic)
        target_size = (300, 300)
        img.thumbnail(target_size, Image.ANTIALIAS)

        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        self.profile_pic.save(self.profile_pic.name, File(buffer), save=False)


