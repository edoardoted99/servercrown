from django.conf import settings as django_settings


def crown_url(request):
    crown_base = django_settings.CROWN_URL
    if crown_base:
        is_secure = crown_base.startswith('https')
        host = crown_base.split('://')[1].rstrip('/')
    else:
        is_secure = request.is_secure() or request.headers.get('X-Forwarded-Proto') == 'https'
        host = request.get_host()

    scheme = 'wss' if is_secure else 'ws'
    return {
        'crown_ws_url': f"{scheme}://{host}/ws/agent/",
    }
