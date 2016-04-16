# -*- coding: utf-8 -*-
"""
A log listening command, with some simple controls.
"""

from __future__ import print_function

import logging
import threading
import collections
import six
import sys
import select
import string
import time

from six.moves.urllib.parse import urlparse as _urlparse, parse_qs

from .utils import ttyraw
from .streams import SplitStreamHandler, ColorLevelFormatter, ColorStreamHandler
from .filters import Filter

class Controller(object):
    """Keyboard input controller for the log listener."""
    
    @classmethod
    def default(cls, logger=""):
        """Default controller, with default configuration, etc."""
        handler = ColorStreamHandler("%(clevelname)s: %(message)s [%(name)s] [%(asctime)s]\r")
        handler.setLevel(1)
        obj = cls(logger, handler)
        return obj
    
    def __init__(self, logger, handler):
        super(Controller, self).__init__()
        if isinstance(logger, six.string_types):
            logger = logging.getLogger(logger)
        self.logger = logger
        self.handler = handler
        self.logger.addHandler(handler)
        self.filter = Filter()
        self.logger.addFilter(self.filter)
        self._shouldrun = threading.Event()
        
    def run(self):
        """Run the controller."""
        allowed_keys = "012345qf"
        allowed_letters = string.digits+string.letters+string.punctuation+" "
        self._shouldrun.set()
        with ttyraw():
            print("Press 0-5 to change logging level. Press q to quit. Press f to change filter.\r")
            while self._shouldrun.isSet():
                ready,_,_ = select.select([sys.stdin],[],[],0.00001)
                if sys.stdin in ready:
                    self.handler.acquire()
                    key = sys.stdin.read(1).lower()
                    if key is not None and key in allowed_keys:
                        self.handler.acquire()
                        if key == "q":
                            self._shouldrun.clear()
                        elif key == "f":
                            print("filter by: ", end="")
                            name = ""
                            new_key = sys.stdin.read(1).lower()
                            while new_key in allowed_letters:
                                sys.stdout.write(new_key)
                                sys.stdout.flush()
                                name += new_key
                                new_key = sys.stdin.read(1).lower()
                            sys.stdout.write("\r\n")
                            sys.stdout.flush()
                            self.filter.name = name
                        else:
                            print("Setting level to {0}\r".format(logging.getLevelName(int(key) * 10)))
                            self.handler.setLevel(int(key) * 10)
                    self.handler.release()
        
    

def urlparse(url):
    """Parse a URL to determine if it is redis-compatible or not."""
    result = _urlparse(url)
    if result.scheme not in SUPPORTED_SCHEMES:
        raise ValueError("URL Scheme {0} not supported by lumberjack.".format(result.scheme))
    return result
    
def setup_redis(url):
    """Set up a redis watcher for a given URL."""
    from .redis import REDISLogWatcher
    return REDISLogWatcher.from_url(url)
    
def setup_zmq(url):
    """Set up a ZMQ watcher for a given URL."""
    from .zmq import ZMQLogWatcher
    return ZMQLogWatcher.from_url(url)

SUPPORTED_SCHEMES = {
    'redis' : setup_redis,
    'unix' : setup_redis,
    'rediss': setup_redis,
    'tcp' : setup_zmq,
    'udp' : setup_zmq,
    'inproc' : setup_zmq,
    'ipc' : setup_zmq,
}

def main(*args):
    """Main function for argument parsing and running log watcher."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=urlparse, help="A URL for a logging stream.")
    parser.add_argument("-c","--channel", type=str, help="Channel to listen for.", default="")
    parser.add_argument("--pickle", action='store_const', help="Use Pickle for seralizing.", dest="serializer", const='pickle')
    parser.add_argument("--json", action='store_const', help="Use Pickle for seralizing.", dest="serializer", const='json')
    opt = parser.parse_args(args)
    setup = SUPPORTED_SCHEMES[opt.url.scheme]
    print("Listening for logging messages on {0}".format(opt.url.geturl()))
    watcher = setup(opt.url.geturl())
    try:
        watcher.subscribe(opt.channel)
        watcher.start()
        control = Controller.default()
        control.run()
    except KeyboardInterrupt:
        print("...ending")
    finally:
        watcher.stop()
    return 0
    