from django.conf import settings

def theme_settings(request):
    return {
        'theme': getattr(settings, 'THEME_SETTINGS', {}),
        'hero_images': [
            'images/default-profile.png',
            'images/house3.jpg'
        ]
    }