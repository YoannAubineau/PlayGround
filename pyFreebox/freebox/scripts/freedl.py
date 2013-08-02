#!/usr/bin/env python
"""Simple downloader."""

#TODO progress bar
#TODO keystroke for detaching
#TODO freedl url --detach
#TODO freedl list
#TODO freedl attach

from __future__ import print_function

import os
import sys
import time

from getpass import getpass
from urlparse import urlparse

import freebox

def main():
    url = sys.argv[1]
    freebox.login(getpass('Freebox password: '))
    dl = freebox.Download(url)
    while dl.status != 'done':
        print(dl.transferred * 100 // max(dl.size, 1))
        time.sleep(1)
    filename = os.path.basename(urlparse(url).path)
    dl.save(filename)
    print('100')
    dl.close()


if __name__ == '__main__':
    main()

