from django.http import HttpResponseForbidden
from django.core.cache import cache

from block_ip.models import BlockIP


def get_ip(req):
    return req.META['REMOTE_ADDR']


def is_ip_in_nets(ip, nets):
    for net in nets:
        if ip in net:
            return True
    return False


class BlockIPMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)

        response = self.get_response(request)

        return response

    def process_request(self, request):
        is_banned = False

        ip = get_ip(request)
        # TODO: Look into something more optimized for large numbers
        # of blocks. https://github.com/jimfunk/django-postgresql-netfields
        block_ips = cache.get('blockip:list')
        if block_ips is None:
            block_ips = BlockIP.objects.all()
            cache.set('blockip:list', block_ips)
        deny_ips = [i.get_network() for i in block_ips]

        for net in deny_ips:
            if ip in net:
                is_banned = True
                break

        if is_banned:
            # delete sessions when denied
            for k in request.session.keys():
                del request.session[k]
            return HttpResponseForbidden("")
