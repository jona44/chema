import os
from .settings import *
from .settings import BASE_DIR

<<<<<<< HEAD
# from azure.identity import DefaultAzureCredential
# import psycopg2
=======

>>>>>>> e0af8f32c711a61879504b7d6d0bf952457570c9


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

<<<<<<< HEAD
# STORAGES = {
#     # ...
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#     },
# }


# Uncomment the following lines according to the authentication type.
# For system-assigned identity.
#credential = DefaultAzureCredential()

# For user-assigned identity.
# managed_identity_client_id = os.getenv('AZURE_POSTGRESQL_CLIENTID')
# cred = ManagedIdentityCredential(client_id=managed_identity_client_id)    

# For service principal.
# tenant_id = os.getenv('AZURE_POSTGRESQL_TENANTID')
# client_id = os.getenv('AZURE_POSTGRESQL_CLIENTID')
# client_secret = os.getenv('AZURE_POSTGRESQL_CLIENTSECRET')
# cred = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)

# Acquire the access token.
#accessToken =credential.get_token('https://ossrdbms-aad.database.windows.net/.default')


# # In your setting file, eg. settings.py
# host = os.getenv('AZURE_POSTGRESQL_HOST')
# user = os.getenv('AZURE_POSTGRESQL_USER')
# password = accessToken.token # this is accessToken acquired from above step.
# database = os.getenv('AZURE_POSTGRESQL_NAME')

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'AZURE_POSTGRESQL_NAME',
#         'USER': 'AZURE_POSTGRESQL_USER',
#         'PASSWORD': 'accessToken',
#         'HOST': 'AZURE_POSTGRESQL_HOST',
#         'PORT': '5432',  # Port is 5432 by default 
#         'OPTIONS': {'sslmode': 'require'},
#     }
# }



#connection_string = os.environ['AZURE_POSTGRESQL_CONNECTIONSTRING']
connection_string = os.environ.get('AZURE_POSTGRESQL_CONNECTIONSTRING')

#connection_string = os.environ['AZURE_POSTGRESQL_CONNECTIONSTRING']
=======
STORAGES =  {
    # ...
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


connection_string = os.environ.get('AZURE_POSTGRESQL_CONNECTIONSTRING')

#connection_string = os.environ['AZURE_POSTGRESQL_CONNECTIONSTRING']
>>>>>>> e0af8f32c711a61879504b7d6d0bf952457570c9
#parameters = {pair.split('='):pair.split('=')(1) for pair in connection_string.split(' ')}
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
<<<<<<< HEAD
# DATABASES = {
#     'default':{
#         'ENGINE':'django.db.backends.postgresql',
#         'NAME':'chemaonline-database ',
#         'HOST':'chemaonline-server.postgres.database.azure.com',
#         'USER':'labcfxiqdd',
#         'PORT': 5432,
#         'SSLMODE':'require',
#         'PASSWORD':'Y1FZAVFH4X38SN7J$'
#     }    
# }
=======

>>>>>>> e0af8f32c711a61879504b7d6d0bf952457570c9

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER ='manyadzatocky@gmail.com'
EMAIL_HOST_PASSWORD  = os.environ['EMAIL_PASSWORD']


 