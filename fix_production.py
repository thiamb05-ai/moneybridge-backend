content = open('moneybridge/settings.py').read()

extra = '''
import dj_database_url
import os

# Production
ALLOWED_HOSTS = ['*']
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Database Railway
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(DATABASE_URL)
'''

with open('moneybridge/settings.py', 'a') as f:
    f.write(extra)
print('settings.py OK')