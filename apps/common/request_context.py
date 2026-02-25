from threading import local

_local_state = local()


def set_current_request(request):
    _local_state.request = request


def get_current_request():
    return getattr(_local_state, 'request', None)
