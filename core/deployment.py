import os
from .settings import *
from .settings import BASE_DIR

SECRET_KEY = os.environ['SECRET']
ALLOWED_HOST = ['WEBSITE_HOSTNAME']
CSRF_TRUSTED_ORIGINS = ['https://'+ os.environ['WEBSITE_HOSTNAME']]

DEBUG = False

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

# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# STATIC_ROOT =os.path.join(BASE_DIR, 'staticfiles')

STORAGES = {
    # ...
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# connection_string = os.environ['AZURE_POSTGRESQL_CONNECTIONSTRING']
connection_string = os.environ.get['AZURE_POSTGRESQL_CONNECTIONSTRING']
# parameters = {pair.split('='):pair.split('=')(1) for pair in connection_string.split(' ')}
parameters = {pair.split('=')[0]: pair.split('=')[1] for pair in connection_string.split(';')}


# DATABASES = {
#     'default':{
#         'ENGINE':'django.db.backends.postgresql',
#         'NAME':parameters["dbname"],
#         'HOST':parameters['host'],
#         'USER':parameters['user'],
#         'PORT':parameters[5432] ,
#         'SSLMODE':parameters['require'],
#         'PASSWORD':parameters['password'],
#     }    
# }
DATABASES = {
    'default':{
        'ENGINE':'django.db.backends.postgresql',
        'NAME':'chemaonline-database ',
        'HOST':'chemaonline-server.postgres.database.azure.com',
        'USER':'labcfxiqdd',
        'PORT': 5432,
        'SSLMODE':'require',
        'PASSWORD':'Y1FZAVFH4X38SN7J$'
    }    
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER ='manyadzatocky@gmail.com'
EMAIL_HOST_PASSWORD  = os.environ['EMAIL_PASSWORD']

WEBSITES_PORT = 8000
WEBSITES_CONTAINER_START_TIME_LIMIT = 1800
 