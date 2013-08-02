"""Download feature."""

import freebox.api

from freebox.utils import save_file


class Download(object):

    def __init__(self, url):
        self.id = freebox.api.download.http_add(url)['result']
        self.info = freebox.api.download.get(self.id)['result']

    def __getattr__(self, name):
        if name not in self.info:
            raise AttributeError(name)
        try:
            self.info = freebox.api.download.get(self.id)['result']
        except KeyError:
            pass
        return self.info[name]

    def pause(self):
        freebox.api.download.stop(self.id)

    def resume(self):
        freebox.api.download.start(self.id)

    def close(self):
        freebox.api.download.remove(self.id)
        
    def save(self, filepath):
        response = freebox.api.download.download(self.info['name'])
        save_file(filepath, response)
        
    def __enter__(self):
        self.resume()
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


__all__ = ['Download']
