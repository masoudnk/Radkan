from threading import current_thread

from django.utils.deprecation import MiddlewareMixin


_requests = {}


def current_request():
    return _requests.get(current_thread().ident, None)
def current_data():
    return _requests.get("data", None)


class RequestMiddleware(MiddlewareMixin):

    def process_request(self, request):
        _requests[current_thread().ident] = request
        _requests["data"] = request.body


    def process_response(self, request, response):
        # when response is ready, request should be flushed
        _requests.pop(current_thread().ident, None)
        return response


    def process_exception(self, request, exception):
        # if an exception has happened, request should be flushed too
         _requests.pop(current_thread().ident, None)