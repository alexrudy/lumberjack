# The following four Getch* classes implement unbuffered character reading from
# stdin on Windows, linux, MacOSX.  This is taken directly from ActiveState
# Code Recipes:
# http://code.activestate.com/recipes/134892-getch-like-unbuffered-character-reading-from-stdin/
#

import contextlib

@contextlib.contextmanager
def ttyraw():
    """Terminal character mode on unix"""
    import sys
    import tty
    import termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
@contextlib.contextmanager
def ttycomposed():
    """Terminal character mode on unix"""
    import sys
    import tty
    import termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(sys.stdin.fileno())
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

class Getch(object):
    """Get a single character from standard input without screen echo.

    Returns
    -------
    char : str (one character)
    """
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            try:
                self.impl = _GetchMacCarbon()
            except (ImportError, AttributeError):
                self.impl = _GetchUnix()

    def __call__(self):
        return self.impl()


class _GetchUnix(object):
    def __init__(self):
        import tty  # pylint: disable=W0611
        import sys  # pylint: disable=W0611

        # import termios now or else you'll get the Unix
        # version on the Mac
        import termios  # pylint: disable=W0611

    def __call__(self):
        import sys
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows(object):
    def __init__(self):
        import msvcrt  # pylint: disable=W0611

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


class _GetchMacCarbon(object):
    """
    A function which returns the current ASCII key that is down;
    if no ASCII key is down, the null string is returned.  The
    page http://www.mactech.com/macintosh-c/chap02-1.html was
    very helpful in figuring out how to do this.
    """
    def __init__(self):
        import Carbon
        Carbon.Evt  # see if it has this (in Unix, it doesn't)

    def __call__(self):
        import Carbon
        if Carbon.Evt.EventAvail(0x0008)[0] == 0:  # 0x0008 is the keyDownMask
            return ''
        else:
            #
            # The event contains the following info:
            # (what,msg,when,where,mod)=Carbon.Evt.GetNextEvent(0x0008)[1]
            #
            # The message (msg) contains the ASCII char which is
            # extracted with the 0x000000FF charCodeMask; this
            # number is converted to an ASCII character with chr() and
            # returned
            #
            (what, msg, when, where, mod) = Carbon.Evt.GetNextEvent(0x0008)[1]
            return chr(msg & 0x000000FF)