def crown_url(request):
    is_secure = request.is_secure() or request.headers.get('X-Forwarded-Proto') == 'https'
    scheme = 'wss' if is_secure else 'ws'
    return {
        'crown_ws_url': f"{scheme}://{request.get_host()}/ws/agent/",
    }
