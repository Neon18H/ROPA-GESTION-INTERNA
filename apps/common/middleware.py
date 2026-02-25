from apps.common.request_context import set_current_request


class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organization = getattr(request.user, 'organization', None) if getattr(request, 'user', None) and request.user.is_authenticated else None
        set_current_request(request)
        return self.get_response(request)
