import os
from decouple import config

# Determine which settings to use based on environment
ENVIRONMENT = config('DJANGO_ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    from .production import *
else:
    from .base import *

# Override settings based on environment variables
if config('DEBUG', default=None, cast=bool) is not None:
    DEBUG = config('DEBUG', cast=bool)

if config('SECRET_KEY', default=None):
    SECRET_KEY = config('SECRET_KEY')

if config('ALLOWED_HOSTS', default=None):
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])