

from pathlib import Path,os

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-l1u#8qmj&mfygs(0exmn%#-=jr8!$5gt5&_7)w@z8wf*ep%!(m'

DEBUG = True

ALLOWED_HOSTS = []


SITE_ID = 0

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'chema',
    'user',
    'crispy_forms',
    "crispy_bootstrap5",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google', 
   
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
        # ...
    },
           
]

# Allauth Settings
AUTHENTICATION_CLASSES = (
    # ...
    'allauth.account.auth_backends.AuthenticationBackend',
    # ...
)

AUTHENTICATION_CLASS = (
    # ...
    'allauth.account.auth_backends.AuthenticationBackend',
    # ...
)


WSGI_APPLICATION = 'core.wsgi.application'


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    # ...
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            "profile",
            "email"
        ],
            "AUTH_PARAMS":{"access_type":"online"}
    }
}


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = 'static/'
 
STATICFILES_DIRS = [
    BASE_DIR, 'static'
    ]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Adjust the path as needed


LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# LOGIN_URL = 'account/login'
# LOGOUT_URL = 'account/logout'




CRISPY_TEMPLATE_PACK = 'bootstrap4'
TEMPLATE_DIRS = [(BASE_DIR, 'templates')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = 'bootstrap5'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER ='manyadzatocky@gmail.com'
EMAIL_HOST_PASSWORD = '@manymore41'

