# -*- coding: utf-8 -*-
"""
Module to allow quick configuration.
"""
from six.moves import configparser
from six import StringIO
import pkg_resources

import logging.config

def configure(mode, disable_existing_loggers=False):
    """Configure from predefined useful default modes."""
    cfg = configparser.ConfigParser()
    modefn = "{0}.cfg".format(mode) if not mode.endswith(".cfg") else mode
    for filename in ["base.cfg", modefn]:
        cfg.readfp(pkg_resources.resource_stream(__name__, filename))
    cfgbuffer = StringIO()
    cfg.write(cfgbuffer)
    cfgbuffer.seek(0)
    return logging.config.fileConfig(cfgbuffer, disable_existing_loggers=disable_existing_loggers)