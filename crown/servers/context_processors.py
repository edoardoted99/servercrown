def crown_url(request):
    scheme = 'wss' if request.is_secure() else 'ws'
    return {
        'crown_ws_url': f"{scheme}://{request.get_host()}/ws/agent/",
    }
