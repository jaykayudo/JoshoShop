from urllib.parse import urlparse

from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.websocket import WebSocketHandler

class NotificationHandler(WebSocketHandler):
    def check_origin(self, origin):
       allowed = super().check_origin(origin)
       parsed = urlparse(origin.lower())
       return allowed or parsed.netloc.startswith('localhost:')
    def open(self, *args: str, **kwargs: str):
        return super().open(*args, **kwargs)
    
    def on_message(self, message):
        return super().on_message(message)
    def on_close(self):
        return super().on_close()
    
