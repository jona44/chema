import os
from .settings import *
from .settings import BASE_DIR


SECRET_KEY = os.environ['SECRET']
ALLOWED_HOST = ['WEBSITE_HOSTNAME']
CSRF_TRUSTED_ORIGINS = ['https://'+ os.environ['WEBSITE_HOSTNAME']]

DEBUG = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT =os.path.join(BASE_DIR, 'staticfiles')



connection_string = os.environ.get('AZURE_POSTGRESQL_CONNECTIONSTRING')


parameters = {pair.split('=')[0]: pair.split('=')[1] for pair in connection_string.split(' ')}


#learn.microsoft.com/en-us/azure/service-connector/how-to-integrate-postgres

DATABASES = {
    'default':{
        'ENGINE':'django.db.backends.postgresql',
        'NAME':parameters["dbname"],
        'HOST':parameters['host'],
        'USER':parameters['user'],
        'PASSWORD':parameters['password'],
    }    
}


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER ='manyadzatocky@gmail.com'
EMAIL_HOST_PASSWORD  = os.environ['EMAIL_PASSWORD']


 
 