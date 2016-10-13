# -*- coding: utf-8 -*-
"""
Lumberjack utilities for logging to streams.
"""

import logging
import types
import sys # Default streams.
import traceback

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
            record.cstart, record.cstop = color_text("=", color).split("=")
        else:
            record.clevelname = record.levelname
            record.cstart, record.cstop = color_text("=", 'default').split("=")
        record.dstart, record.dstop = color_text("=", 'default').split("=")
        return super(ColorLevelFormatter, self).format(record)
        

class SplitStreamHandler(logging.StreamHandler, object):
    """Split info vs. error to stdout and stderr"""
    
    def __init__(self):
        super(SplitStreamHandler, self).__init__()
        del self.stream
        self._ttyraw = False
        
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
            if self._ttyraw:
                fs = "%s\r\n"
                msg = msg.replace("\n","\r\n")
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
        
    def handleError(self, record):
        """
        Handle errors which occur during an emit() call.

        This method should be called from handlers when an exception is
        encountered during an emit() call. If raiseExceptions is false,
        exceptions get silently ignored. This is what is mostly wanted
        for a logging system - most users will not care about errors in
        the logging system, they are more interested in application errors.
        You could, however, replace this with a custom handler if you wish.
        The record which was being processed is passed in to this method.
        """
        if logging.raiseExceptions and sys.stderr:  # see issue 13807
            t, v, tb = sys.exc_info()
            try:
                sys.stderr.write('--- Logging error ---\n')
                traceback.print_exception(t, v, tb, None, sys.stderr)
                sys.stderr.write('Call stack:\n')
                # Walk the stack frame up until we're out of logging,
                # so as to print the calling context.
                frame = tb.tb_frame
                while (frame and os.path.dirname(frame.f_code.co_filename) ==
                       __path__[0]):
                    frame = frame.f_back
                if frame:
                    traceback.print_stack(frame, file=sys.stderr)
                else:
                    # couldn't find the right stack frame, for some reason
                    sys.stderr.write('Logged from file %s, line %s\n' % (
                                     record.filename, record.lineno))
                # Issue 18671: output logging message and arguments
                try:
                    sys.stderr.write('Message: %r\n'
                                     'Arguments: %s\n' % (record.msg,
                                                          record.args))
                except Exception:
                    sys.stderr.write('Unable to print the message and arguments'
                                     ' - possible formatting error.\nUse the'
                                     ' traceback above to help find the error.\n'
                                    )
            except OSError: #pragma: no cover
                pass    # see issue 5971
            finally:
                del t, v, tb

class ColorStreamHandler(SplitStreamHandler):
    """A SplitStreamHandler which defaults to having the ColorStreamFormatter."""
    def __init__(self, fmt=None, datefmt=None):
        super(ColorStreamHandler, self).__init__()
        self.setFormatter(ColorLevelFormatter(fmt=fmt, datefmt=datefmt))
        