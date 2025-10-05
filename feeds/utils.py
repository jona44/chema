# feeds/utils.py

from django.core.files.base import ContentFile
from django.conf import settings
from PIL import Image, ImageOps
import os
import mimetypes
from io import BytesIO
import uuid


def validate_media_file(file, post_type):
    """Validate uploaded media file"""
    # Check file size
    max_size = getattr(settings, 'MAX_MEDIA_FILE_SIZE', 50 * 1024 * 1024)  # 50MB default
    if file.size > max_size:
        return False
    
    # Check file type
    mime_type, _ = mimetypes.guess_type(file.name)
    if not mime_type:
        return False
    
    if post_type == 'photo':
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    elif post_type == 'video':
        allowed_types = ['video/mp4', 'video/webm', 'video/ogg', 'video/avi', 'video/quicktime']
    else:
        return False
    
    return mime_type in allowed_types


def process_media_file(file, post_type):
    """Process uploaded media file - resize, optimize, generate thumbnails"""
    metadata = {
        'file_size': file.size,
        'original_name': file.name
    }
    
    if post_type == 'photo':
        return process_image_file(file, metadata)
    elif post_type == 'video':
        return process_video_file(file, metadata)
    else:
        return file, None, metadata


def process_image_file(file, metadata):
    """Process and optimize image file"""
    try:
        # Open and process the image
        image = Image.open(file)
        
        # Convert to RGB if necessary (for JPEG compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Auto-rotate based on EXIF data
        image = ImageOps.exif_transpose(image)
        
        # Resize if too large
        max_size = getattr(settings, 'MAX_IMAGE_DIMENSIONS', (2048, 2048))
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save optimized image
        output = BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        # Generate filename
        file_extension = '.jpg'
        filename = f"posts/{uuid.uuid4().hex}{file_extension}"
        
        optimized_file = ContentFile(output.getvalue(), name=filename)
        
        # Generate thumbnail
        thumbnail = generate_image_thumbnail(image)
        
        metadata.update({
            'dimensions': image.size,
            'format': 'JPEG'
        })
        
        return optimized_file, thumbnail, metadata
        
    except Exception as e:
        # If processing fails, return original file
        return file, None, metadata


def generate_image_thumbnail(image, size=(300, 300)):
    """Generate thumbnail for image"""
    try:
        # Create thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Save thumbnail
        output = BytesIO()
        thumbnail.save(output, format='JPEG', quality=75)
        output.seek(0)
        
        filename = f"thumbnails/{uuid.uuid4().hex}.jpg"
        return ContentFile(output.getvalue(), name=filename)
        
    except Exception:
        return None


def process_video_file(file, metadata):
    """Process video file - basic processing, generate thumbnail"""
    # For video processing, you might want to use ffmpeg-python or similar
    # For now, we'll keep it simple and just handle the basic file operations
    
    try:
        # Generate filename
        file_extension = os.path.splitext(file.name)[1].lower()
        if not file_extension:
            file_extension = '.mp4'
        
        filename = f"posts/videos/{uuid.uuid4().hex}{file_extension}"
        
        # For thumbnail generation from video, you'd need ffmpeg
        # For now, we'll return None for thumbnail
        thumbnail = None
        
        # You could add video duration extraction here using ffmpeg-python
        # metadata['duration'] = get_video_duration(file)
        
        return ContentFile(file.read(), name=filename), thumbnail, metadata
        
    except Exception as e:
        return file, None, metadata


def get_video_duration(video_file):
    """Get video duration in seconds using ffmpeg (optional)"""
    # This would require ffmpeg-python package
    # import ffmpeg
    # try:
    #     probe = ffmpeg.probe(video_file.temporary_file_path())
    #     duration = float(probe['streams'][0]['duration'])
    #     return int(duration)
    # except:
    #     return None
    return None


def generate_video_thumbnail(video_file):
    """Generate thumbnail from video using ffmpeg (optional)"""
    # This would require ffmpeg-python package
    # You could extract a frame at a specific time and create a thumbnail
    return None