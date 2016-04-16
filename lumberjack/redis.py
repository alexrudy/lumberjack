# -*- coding: utf-8 -*-

import six
import logging
from six.moves.urllib.parse import urlparse as urlparse, parse_qs, urlencode

from .serialize import serializers

__all__ = ['REDISLogWatcher', 'REDISPublisher']

def _handle_redis_client_args(args):
    """Handle arguments that should produce a REDIS client."""
    import redis
    if isinstance(args, redis.Redis):
        client = args
    elif isinstance(args, redis.ConnectionPool):
        client = redis.StrictRedis(connection_pool=args)
    elif isinstance(args, tuple):
        host, port = args
        client = redis.StrictRedis(host, port)
    else:
        client = redis.StrictRedis.from_url(args)
    return client

class REDISPublisher(logging.Handler, object):
    """A REDIS publisher, which takes formatted log messages and publishes them to REDIS."""
    def __init__(self, address, channel):
        super(REDISPublisher, self).__init__()
        self.client = _handle_redis_client_args(address)
        self.channel = six.text_type(channel)
        
    def emit(self, record):
        """Emit a single record."""
        try:
            msg = self.format(record)
            self.client.publish(self.channel, msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
        
    

class REDISLogWatcher(object):
    """Watch a REDIS channel for logging"""
    def __init__(self, address, channel, deserialize=None, logger=None):
        super(REDISLogWatcher, self).__init__()
        self.client = _handle_redis_client_args(address)
        self.channels = [six.text_type(channel)]
        self.deserialize = deserialize if deserialize is not None else serializers['pickle'].deserialize
        if isinstance(logger, six.string_types):
            logger = logging.getLogger(logger)
        self._logger = logger
        self.thread = None
        
    @classmethod
    def from_url(cls, url):
        """Create the log watcher from a URL"""
        result = urlparse(url)
        options = parse_qs(result.query)
        channel = options.get("channel", "")
        serializer = serializers[options.get("serialize", "json")]
        if 'db' in options:
            result.query = urlencode([('db', options['db'])])
        else:
            result.query = ''
        url = result.geturl()
        return cls(url, channel, serializer.deserialize)
    
    @property
    def logger(self):
        """Get a logger instance suitable for adjusting the REDIS logger settings."""
        if self._logger is None:
            return logging.getLogger()
        else:
            return self._logger
    
    def _redis_responder(self, msg):
        """Given a REDIS message, create the logrecord and handle it."""
        if msg['channel'] in self.channels:
            record = self.deserialize(msg['data'])
            if self._logger is None:
                logging.getLogger(record.name).handle(record)
            else:
                self.logger.handle(record)
    
    def subscribe(self, name):
        """Subscribe to an addtional channel."""
        self.channels.append(name)
    
    def start(self):
        """Start the log watcher."""
        pubsub = self.client.pubsub()
        for channel in self.channels:
            pubsub.subscribe(**{channel:self._redis_responder})
        self.thread = pubsub.run_in_thread(sleep_time=0.01)
    
    def stop(self):
        """Stop the log watcher"""
        if self.thread is not None:
            self.thread.stop()
        
    def __del__(self):
        """Remove the child thread if necessary."""
        if hasattr(self.thread, 'stop'):
            self.thread.stop()
