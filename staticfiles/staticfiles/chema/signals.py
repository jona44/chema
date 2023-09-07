from django.db.models.signals import pre_save
from django.dispatch import receiver
import random
from .models import Group

@receiver(pre_save, sender=Group)
def set_random_cover_pic(sender, instance, **kwargs):
    if not instance.cover_pic: # check if cover_pic is empty
        images = ['cover 1.jpg', 'cover 2.jpg', 'cover 3.jpg','cover 4.jpg', 
                  'cover 5.jpg', 'cover 6.jpg','cover 7.jpg', 'cover 8.jpg', 'cover 9.jpg'] # list of images in your static directory
        instance.cover_pic = random.choice(images) # assign a random image to cover_pic
