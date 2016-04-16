# -*- coding: utf-8 -*-
"""
Lumberjack utilities for logging to streams.
"""

import logging
import types
import sys # Default streams.

__all__ = ['ColorLevelFormatter', 'SplitStreamHandler', 'ColorStreamHandler']

def color_text(text, color):
    """
    Returns a string wrapped in ANSI color codes for coloring the
    text in a terminal::

        colored_text = color_text('Here is a message', 'blue')

    This won't actually effect the text until it is printed to the
    terminal.

    Parameters
    ----------
    text : str
        The string to return, bounded by the color codes.
    color : str
        An ANSI terminal color name. Must be one of:
        black, red, green, brown, blue, magenta, cyan, lightgrey,
        default, darkgrey, lightred, lightgreen, yellow, lightblue,
        lightmagenta, lightcyan, white, or '' (the empty string).
    """
    color_mapping = {
        'black': '0;30',
        'red': '0;31',
        'green': '0;32',
        'brown': '0;33',
        'blue': '0;34',
        'magenta': '0;35',
        'cyan': '0;36',
        'lightgrey': '0;37',
        'default': '0;39',
        'darkgrey': '1;30',
        'lightred': '1;31',
        'lightgreen': '1;32',
        'yellow': '1;33',
        'lightblue': '1;34',
        'lightmagenta': '1;35',
        'lightcyan': '1;36',
        'white': '1;37'}

    if sys.platform == 'win32':
        # On Windows do not colorize text
        return text
    
    color_code = color_mapping.get(color, '0;39')
    return '\033[{0}m{1}\033[0m'.format(color_code, text)

class ColorLevelFormatter(logging.Formatter, object):
    """A formatter for colors."""
    
    def __init__(self, *args, **kwargs):
        colors = kwargs.pop('colors', None)
        super(ColorLevelFormatter, self).__init__(*args, **kwargs)
        if colors is not None:
            self._level_color_mapping = dict(colors)
        
    
    _level_color_mapping = {
        logging.DEBUG : 'magenta',
        logging.INFO : 'green',
        logging.WARN : 'yellow',
        logging.ERROR : 'red'
    }
    
    def get_color(self, levelno):
        """For a level number, get the color."""
        if not hasattr(self, '_color_levels'):
            self._color_levels = list(sorted(self._level_color_mapping.keys()))
        color = None
        for color_level in self._color_levels:
            if levelno >= color_level:
                color = self._level_color_mapping[color_level]
            else:
                break
        return color
    
    def format(self, record):
        """Override message formatting, to colorize level names."""
        
        color = self.get_color(record.levelno)
        if color is not None:
            record.clevelname = color_text(record.levelname, color)
        else:
            record.clevelname = record.levelname
        
        return super(ColorLevelFormatter, self).format(record)
        

class SplitStreamHandler(logging.StreamHandler, object):
    """Split info vs. error to stdout and stderr"""
    
    def __init__(self):
        super(SplitStreamHandler, self).__init__()
        del self.stream
        
    def flush(self):
        """
        Flushes the stream.
        """
        self.acquire()
        try:
            for stream in [sys.stderr, sys.stdout]:
                if stream and hasattr(stream, "flush"):
                    stream.flush()
        finally:
            self.release()
    
    def emit(self, record):
        """
        Emit a record.
        """
        try:
            msg = self.format(record)
            stream = sys.stdout if record.levelno <= logging.INFO else sys.stderr
            fs = "%s\n"
            if not hasattr(types, "UnicodeType"): #if no unicode support...
                stream.write(fs % msg)
            else:
                try:
                    if (isinstance(msg, unicode) and
                        getattr(stream, 'encoding', None)):
                        fs = fs.decode(stream.encoding)
                        try:
                            stream.write(fs % msg)
                        except UnicodeEncodeError:
                            #Printing to terminals sometimes fails. For example,
                            #with an encoding of 'cp1251', the above write will
                            #work if written to a stream opened or wrapped by
                            #the codecs module, but fail when writing to a
                            #terminal even when the codepage is set to cp1251.
                            #An extra encoding step seems to be needed.
                            stream.write((fs % msg).encode(stream.encoding))
                    else:
                        stream.write(fs % msg)
                except UnicodeError:
                    stream.write(fs % msg.encode("UTF-8"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
        
    

class ColorStreamHandler(SplitStreamHandler):
    """A SplitStreamHandler which defaults to having the ColorStreamFormatter."""
    def __init__(self, *args, **kwargs):
        super(ColorStreamHandler, self).__init__()
        self.setFormatter(ColorLevelFormatter(*args, **kwargs))
        