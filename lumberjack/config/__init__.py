# -*- coding: utf-8 -*-
"""
Module to allow quick configuration.
"""
import six
from six.moves import configparser
from six import StringIO
import pkg_resources

import logging.config

def _get_configbuffer(mode, cfg=None, filenames=None):
    """Get the configuration buffer."""
    cfg = cfg or configparser.ConfigParser()
    modefn = "{0}.cfg".format(mode) if not mode.endswith(".cfg") else mode
    for filename in ["base.cfg", modefn]:
        if six.PY2:
            cfg.readfp(pkg_resources.resource_stream(__name__, filename))
        else:
            import io
            cfg.read_file(io.TextIOWrapper(pkg_resources.resource_stream(__name__, filename)))
    if filenames is None:
        filenames = ['lumberjack.cfg']
    for filename in filenames:
        cfg.read(filename)
    cfgbuffer = StringIO()
    cfg.write(cfgbuffer)
    cfgbuffer.seek(0)
    return cfgbuffer

def configure(mode, disable_existing_loggers=False, cfg=None, filenames=None):
    """Configure from predefined useful default modes."""
    cfgbuffer = _get_configbuffer(mode, cfg=cfg, filenames=filenames)
    return logging.config.fileConfig(cfgbuffer, disable_existing_loggers=disable_existing_loggers)