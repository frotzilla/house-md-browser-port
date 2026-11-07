"""Local static server for the web port. Python's default http.server has a
listen backlog of 5, and the game requests dozens of files at once on startup,
so connections get reset. This raises the backlog and serves .wasm correctly."""
import sys, functools
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

class Server(ThreadingHTTPServer):
    request_queue_size = 256
    daemon_threads = True

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".wasm": "application/wasm"}
    def log_message(self, fmt, *args):
        if len(args) > 1 and str(args[1])[:1] in "45":
            super().log_message(fmt, *args)

port, root = int(sys.argv[1]), sys.argv[2]
Server(("127.0.0.1", port), functools.partial(Handler, directory=root)).serve_forever()
