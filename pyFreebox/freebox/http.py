"""Low-level communication to Freebox through HTTP."""

import json
import urllib2

from contextlib import closing
from urllib import urlencode

from freebox.utils import FreeboxException


class WrongPassword(FreeboxException):
    pass


class DeadHTTPRedirectHandler(urllib2.HTTPRedirectHandler):

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)


class Stub(object):

    def __init__(self):
        self.opener = urllib2.build_opener(DeadHTTPRedirectHandler)
        self.opener.add_handler(urllib2.HTTPCookieProcessor())
        self.urlopen = self.opener.open

    def login(self, password):
        r = self.post('http://mafreebox.freebox.fr/login.php', {
            'login': 'freebox',
            'passwd': password,
        })
        if not r['result']:
            raise WrongPassword()

    def get(self, url, params, as_file=False):
        #XXX log request
        url = '{}?{}'.format(url, urlencode(params))
        return self._request(urllib2.Request(url), as_file)

    def post(self, url, params, as_file=False):
        #print url, params  #XXX log request
        if 'jsonrpc' in params:
            return self._request(urllib2.Request(url, json.dumps(params), {
                'Referer': 'http://mafreebox.freebox.fr',
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }), as_file)
        else:
            return self._request(urllib2.Request(url, urlencode(params), {
                'Referer': 'http://mafreebox.freebox.fr',
                'X-Requested-With': 'XMLHttpRequest',
            }), as_file)

    def _request(self, request, as_file=False):
        response = self.urlopen(request)
        if as_file:
            return response
        with closing(response):
            content = response.read()
            if response.info().getheader('Content-Type') == 'application/json':
                content = json.loads(content)
        return content


__default_stub = None


def login(password):
    stub = Stub()
    stub.login(password)
    global __default_stub
    __default_stub = stub


def post(*args, **kwargs):
    return __default_stub.post(*args, **kwargs)


def get(*args, **kwargs):
    return __default_stub.get(*args, **kwargs)

