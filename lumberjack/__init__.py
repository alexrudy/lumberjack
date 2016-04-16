# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

__version__ = "0.2.1"

import logging
import warnings
import sys, types
from astropy.utils.console import color_print, _color_text
from six.moves import cPickle
import json
import six
from logging import *

def setup_logging(name="", mode='stream', configuration=None, increment=False, level=1):
    """Set up the default interface for logging with ShadyAO."""
    #TODO: This function should become more flexible when used in
    # the installed environment.
    logging.addLevelName(5, "MSG")
    
    root_logger = logging.getLogger(name)
    
    if not (len(root_logger.handlers) == 0 or increment):
        # If there are no handlers, or if increment=True
        # then we want to set up logging. Otherwise, this
        # command should do absolutely nothing!
        return
    if mode == 'stream':
        h = SplitStreamHandler()
        h.setFormatter(ColorFormatter("%(clevelname)s: %(message)s [%(name)s]"))
    elif mode == 'redis':
        address = (configuration.get("redis", "host"), configuration.get("redis", "port"))
        h = REDISPublisher(address, "logging:{0}".format(name))
        if configuration.get("redis", "logging") == "json":
            h.setFormatter(JSONFormatter())
        elif configuration.get("redis", "logging") == "pickle":
            h.setFormatter(PickleFormatter())
    elif mode == 'none':
        if not hasattr(logging, 'NullHandler'):
            #PRAGMA 2.6
            return
        h = logging.NullHandler()
    
    h.setLevel(level)
    root_logger.addHandler(h)
    root_logger.setLevel(1)
    root_logger.propagate = False
    if name:
        couple_loggers(name, "py.warnings")
        setup_warnings_logger(name)
    return root_logger
    
def showwarning_lumberjack(message, category, filename, lineno, line=None, file=None):
    """Adjust warnings formatting."""
    logger = getLogger("py.warnings")
    if not logger.handlers and hasattr(logging, 'NullHandler'):
        logger.addHandler(logging.NullHandler())
    logger.warning("{0} [{1}]".format(message, category.__name__))
    
def setup_warnings_logger(name=""):
    """Set up the warnings logger"""
    root_logger = logging.getLogger(name)
    warnings_logger = logging.getLogger("py.warnings")
    warnings_logger.setLevel(logging.WARNING)
    warnings.showwarning = showwarning_lumberjack
    
def couple_loggers(src, dest):
    """Couple loggers."""
    src = logging.getLogger(src)
    dest = logging.getLogger(dest)
    for handler in src.handlers:
        dest.addHandler(handler)
    dest.setLevel(src.getEffectiveLevel())
    
def get_redis_listener(name="ShadyAO", configuration=None):
    """Make a redis listener for ShadyAO"""
    h = SplitStreamHandler()
    h.setFormatter(ColorFormatter("%(clevelname)s: %(message)s [%(name)s] [%(asctime)s]"))
    
    address = (configuration.get("redis", "host"), configuration.get("redis", "port"))
    rl = REDISLogWatcher(address, "logging:{0}".format(name), makeLogRecord_from_json)
    
    h.setLevel(configuration.getloglevel('logging', 'level'))
    rl.logger.addHandler(h)
    rl.logger.setLevel(1)
    return rl

