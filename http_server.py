from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import os,  threading,  socket
from Queue import Queue
from time import time
from random import *
import string

class ThreadPoolMixIn(ThreadingMixIn):
    numThreads = 100
    allow_reuse_address = True  
    def serve_forever(self):
        self.requests = Queue(self.numThreads)
        for x in range(self.numThreads):
            t = threading.Thread(target = self.process_request_thread)
            t.setDaemon(1)
            t.start()
        while True:
            self.handle_request()
        self.server_close()
    
    def process_request_thread(self):
        while True:
            ThreadingMixIn.process_request_thread(self, *self.requests.get())
    
    def handle_request(self):
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        if self.verify_request(request, client_address):
            self.requests.put((request, client_address))

class Handler(BaseHTTPRequestHandler):
    
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(self):
        try:
            path_split = self.path.split('/')
            self.do_HEAD()
            # If path matches 'get_data' then send some test data
            if path_split[1] == 'get_data':
                
                # Reply with random string:
                reply_data = "".join(choice(string.ascii_letters + string.punctuation) for x in range(0, 100))
                data = json.dumps({'data': reply_data})
                self.wfile.write(data.encode())
                
            #size = int(self.path.split('/')[1])
            #self.send_response(200)
            #self.end_headers()
            #payload = os.urandom(size)
            #self.wfile.write(payload)
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)
        #except ValueError:
            #self.send_error(404, 'Page Not Found: %s' % self.path)

class ThreadedHTTPServer(ThreadPoolMixIn, HTTPServer):
    pass

if __name__ == '__main__':
    server = ThreadedHTTPServer(('', 80), Handler)
    print ('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()

