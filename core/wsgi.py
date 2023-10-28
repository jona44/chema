import os
from django.core.wsgi import get_wsgi_application

settings_module = 'core.deployment' if 'WEBSITE_HOSTNAME' in os.environ else 'core.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE',' core.settings' )

application = get_wsgi_application()
