"""
Django settings for Elite Wealth Capital project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Load environment variables
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security Settings
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1,elitewealthcapita.uk,www.elitewealthcapita.uk,portal.elitewealthcapita.uk,my-site-gbql.onrender.com'
).split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://elitewealthcapita.uk',
    'https://www.elitewealthcapita.uk',
    'https://portal.elitewealthcapita.uk',
    'https://my-site-gbql.onrender.com'
]

# Application definition
INSTALLED_APPS = [
    # Modern Admin UI - MUST be before django.contrib.admin
    'jazzmin',
    
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third Party
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'django_ratelimit',
    'storages',  # Django-storages for R2/S3
    
    # Local Apps
    'accounts',
    'investments',
    'dashboard',
    'kyc',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files
    'elite_wealth_capital.bot_protection.BotProtectionMiddleware',  # Block malicious bots
    'elite_wealth_capital.bot_protection.IPBlockMiddleware',  # Block malicious IPs
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'elite_wealth_capital.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'elite_wealth_capital.context_processors.site_settings',
                'elite_wealth_capital.context_processors.tawk_settings',
                'elite_wealth_capital.context_processors.notification_context',
                'elite_wealth_capital.context_processors.user_stats',
                'elite_wealth_capital.context_processors.page_type',
            ],
        },
    },
]

WSGI_APPLICATION = 'elite_wealth_capital.wsgi.application'

# Database
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Authentication Backends - allows login with email or 'admin' username
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# ============ MEDIA FILES - CLOUDFLARE R2 STORAGE ============
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============ CLOUDFLARE R2 CONFIGURATION (S3-Compatible) ============
# R2 credentials
AWS_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', 'elite-wealth-media')

# R2 endpoint (NOT AWS S3!)
AWS_S3_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL', '')  # https://ACCOUNT_ID.r2.cloudflarestorage.com
AWS_S3_CUSTOM_DOMAIN = os.getenv('R2_CUSTOM_DOMAIN', '')  # Optional: media.elitewealthcapita.uk

# S3 configuration
AWS_S3_REGION_NAME = 'auto'  # R2 uses 'auto'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = 'private'  # Keep files private
AWS_QUERYSTRING_AUTH = True  # Generate signed URLs for private files
AWS_QUERYSTRING_EXPIRE = 3600  # Signed URL expires in 1 hour

# Performance
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # Cache for 24 hours
}

# Use R2 for media files in production
if not DEBUG and AWS_ACCESS_KEY_ID:
    DEFAULT_FILE_STORAGE = 'elite_wealth_capital.storage_backends.R2MediaStorage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN or AWS_STORAGE_BUCKET_NAME}/'
else:
    # Use local storage in development
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'apikey')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'admin@elitewealthcapita.uk')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@elitewealthcapita.uk')

# Company Information
COMPANY_NAME = os.getenv('COMPANY_NAME', 'Elite Wealth Capital')
COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', 'admin@elitewealthcapita.uk')
COMPANY_PHONE = os.getenv('COMPANY_PHONE', '+47 22 33 44 55')
COMPANY_ADDRESS = os.getenv('COMPANY_ADDRESS', 'London, United Kingdom')
COMPANY_WEBSITE = os.getenv('COMPANY_WEBSITE', 'https://elitewealthcapita.uk')

# Tawk.to Live Chat
TAWK_PROPERTY_ID = os.getenv('TAWK_PROPERTY_ID', '')
TAWK_WIDGET_ID = os.getenv('TAWK_WIDGET_ID', '')
TAWK_API_KEY = os.getenv('TAWK_API_KEY', '')

# Cache Configuration (improves performance)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes
    }
}

# Rate limit settings - use locmem for dev, Redis recommended for production
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_FAIL_OPEN = True  # Don't block if cache is unavailable

# Silence ratelimit cache warnings for development (use Redis in production)
SILENCED_SYSTEM_CHECKS = ['django_ratelimit.E003', 'django_ratelimit.W001']

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Database connection optimization
CONN_MAX_AGE = 60  # Keep connections alive for 60 seconds

# Security Settings (Production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Content Security Policy - blocks unauthorized scripts
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    
    # Additional security headers
    X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# CORS Settings - Never allow all origins in production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'https://elitewealthcapita.uk',
    'https://www.elitewealthcapita.uk',
    'https://my-site-ghnp.onrender.com',
]

# Session Settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True

# Messages Framework
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Login/Logout URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Jazzmin Admin Settings
JAZZMIN_SETTINGS = {
    "site_title": "Elite Wealth Admin",
    "site_header": "Elite Wealth Capital",
    "site_brand": "Admin Panel",
    "site_logo": "images/logo.webp",
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "Elite Wealth Capital - Admin Panel",
    "copyright": "Elite Wealth Capital Ltd. - Separate Admin System",
    "search_model": ["accounts.CustomUser", "investments.Investment", "investments.Deposit"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Users", "url": "admin:accounts_customuser_changelist"},
        {"name": "Deposits", "url": "admin:investments_deposit_changelist"},
        {"name": "Withdrawals", "url": "admin:investments_withdrawal_changelist"},
        {"name": "Wallets", "url": "admin:investments_walletaddress_changelist"},
        {"name": "View Site", "url": "/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "accounts",
        "accounts.CustomUser",
        "investments",
        "investments.Deposit",
        "investments.Withdrawal",
        "investments.Investment",
        "investments.WalletAddress",
        "investments.InvestmentPlan",
        "kyc",
        "notifications",
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "accounts": "fas fa-user-shield",
        "accounts.CustomUser": "fas fa-user-circle",
        "accounts.ActivityLog": "fas fa-history",
        "accounts.Referral": "fas fa-user-friends",
        "investments": "fas fa-coins",
        "investments.InvestmentPlan": "fas fa-list",
        "investments.Investment": "fas fa-chart-line",
        "investments.Deposit": "fas fa-money-bill-wave",
        "investments.Withdrawal": "fas fa-hand-holding-dollar",
        "investments.WalletAddress": "fas fa-wallet",
        "investments.Loan": "fas fa-handshake",
        "investments.VirtualCard": "fas fa-credit-card",
        "investments.Coupon": "fas fa-ticket",
        "investments.AgentApplication": "fas fa-user-tie",
        "investments.AccountUpgrade": "fas fa-arrow-up",
        "kyc": "fas fa-id-card",
        "kyc.KYCDocument": "fas fa-file-lines",
        "notifications": "fas fa-bell",
        "notifications.Notification": "fas fa-envelope",
        "dashboard": "fas fa-gauge-high",
        "dashboard.SiteSettings": "fas fa-cogs",
    },
    "default_icon_parents": "fas fa-circle-chevron-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
        "accounts.customuser": "horizontal_tabs",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "default",
    "default_theme_mode": "light",  # Updated from deprecated dark_mode_theme
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
