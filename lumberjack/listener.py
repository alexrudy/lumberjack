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
        handler = ColorStreamHandler("%(clevelname)s: %(message)s [%(name)s] [%(asctime)s]")
        handler.setLevel(1)
        handler._ttyraw = True
        obj = cls(logger, handler)
        return obj
    
    def __init__(self, logger, handler, stdin=sys.stdin, stdout=sys.stdout):
        super(Controller, self).__init__()
        
        self._shouldrun = threading.Event()
        
        if isinstance(logger, six.string_types):
            logger = logging.getLogger(logger)
        self.logger = logger
        self.handler = handler
        self.logger.addHandler(handler)
        self.filter = Filter()
        self.handler.addFilter(self.filter)
        
        self.stdin = stdin
        self.stdout = stdout
        
    def echo(self, items):
        """Echo items to stdout."""
        self.stdout.write(items)
        self.stdout.flush()
        
    def _filter_input(self):
        """Accept input as a filter."""
        backspaces = "\x08\x7f"
        allowed_letters = string.digits+string.letters+string.punctuation+" "+backspaces
        self.echo("Set filter: ")
        key = self.stdin.read(1)
        filtername = []
        while key in allowed_letters:
            if key is not None:
                if key in backspaces:
                    filtername.pop()
                    self.echo("\b \b")
                else:
                    filtername.append(key)
                    self.echo(key)
            ready,_,_ = select.select([self.stdin],[],[],10)
            if self.stdin in ready:
                key = self.stdin.read(1)
            else:
                break
        else:
            self.filter.name = "".join(filtername)
        self.echo("\n\rFiltering for '{:s}'\n\r".format(self.filter.name))
        return
        
    def run(self):
        """Run the controller."""
        allowed_keys = "012345q"
        allowed_letters = string.digits+string.letters+string.punctuation+" "
        self._shouldrun.set()
        with ttyraw():
            self.echo("Press 0-5 to change logging level. Press q to quit.\n\r")
            while self._shouldrun.isSet():
                ready,_,_ = select.select([self.stdin],[],[],0.1)
                if self.stdin in ready:
                    self.handler.acquire()
                    try:
                        key = self.stdin.read(1)
                        if key is not None:
                            if key.lower() in allowed_keys:
                                if key.lower() == "q":
                                    self._shouldrun.clear()
                                elif key.lower() == "f":
                                    self._filter_input()
                                else:
                                    self.echo("Setting level to {0}\n\r".format(logging.getLevelName(int(key) * 10)))
                                    self.handler.setLevel(int(key) * 10)
                            elif key not in string.printable:
                                self.echo("^C")
                                raise KeyboardInterrupt("Got unknown character {!r}.".format(key))
                    finally:
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

def setup(mode, url):
    """Set up a logger for a given mode and URL"""
    return SUPPORTED_SCHEMES[mode](url)
    
def logging_level(input):
    """Parse logging level as input."""
    try:
        return int(getattr(logging, input.upper()))
    except (TypeError, AttributeError):
        pass
    try:
        return int(input)
    except TypeError:
        raise ValueError("Logging level '{:s}' unknown.".format(input))
    

def main(*args):
    """Main function for argument parsing and running log watcher."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=urlparse, help="A URL for a logging stream.")
    parser.add_argument("-c","--channel", type=str, help="Channel to listen for.", default="")
    parser.add_argument("-l","--level", type=logging_level, help="Logging level", default=1)
    parser.add_argument("--pickle", action='store_const', help="Use Pickle for seralizing.", dest="serializer", const='pickle')
    parser.add_argument("--json", action='store_const', help="Use Pickle for seralizing.", dest="serializer", const='json')
    opt = parser.parse_args(args)
    print("Listening for logging messages on {0}".format(opt.url.geturl()))
    watcher = setup(opt.url.scheme, opt.url.geturl())
    try:
        watcher.subscribe(opt.channel)
        watcher.start()
        controller = Controller.default()
        controller.run()
    except KeyboardInterrupt:
        print("...ending")
    finally:
        watcher.stop()
    return 0
    
if __name__ == '__main__':
    main()
    