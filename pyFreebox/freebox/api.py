# -*- coding: utf8 -*-
"""Object implementation of Freebox API."""

from datetime import timedelta

import freebox.http

from freebox.utils import Memoize


class download:
    
    url = 'http://mafreebox.freebox.fr/download.cgi'

    @classmethod
    def http_add(cls, url):
        return freebox.http.post(cls.url, {
            'user': 'freebox',
            'method': 'download.http_add',
            'url': url,
        })

    @classmethod
    @Memoize(timedelta(seconds=1))
    def list(cls):
        return freebox.http.post(cls.url, {
            'jsonrpc': '2.0',
            'method': 'download.list',
        })
        
    @classmethod
    @Memoize(timedelta(seconds=1))
    def get(cls, id):
        return freebox.http.post(cls.url, {
            'jsonrpc': '2.0',
            'method': 'download.get',
            'params': ['http', id],
        })

    @classmethod
    def start(cls, id):
        return freebox.http.post(cls.url, {
            'jsonrpc': '2.0',
            'method': 'download.start',
            'params': ['http', id],
        })
        
    @classmethod
    def stop(cls, id):
        return freebox.http.post(cls.url, {
            'jsonrpc': '2.0',
            'method': 'download.stop',
            'params': ['http', id],
        })

    @classmethod
    def remove(cls, id):
        return freebox.http.post(cls.url, {
            'jsonrpc': '2.0',
            'method': 'download.remove',
            'params': ['http', id],
        })

    @classmethod
    def download(cls, filename):
        return freebox.http.post('http://mafreebox.freebox.fr/get.php', {
            'filename': '/Disque dur/Téléchargements/{}'.format(filename),
        }, as_file=True)
