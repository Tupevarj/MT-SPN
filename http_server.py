from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import os, threading, socket
from Queue import Queue
import json
from random import *
import string
import re
from threading import Thread
import datetime
import requests

request_counter = 0

class ThreadPoolMixIn(ThreadingMixIn):
    numThreads = 100
    allow_reuse_address = True

    def serve_forever(self):
        self.requests = Queue(self.numThreads)
        for x in range(self.numThreads):
            t = threading.Thread(target=self.process_request_thread)
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


class RequestCounter:
    """ Keeps list of all counts time interval, that is set through timeout variable.
        Updates automatically when counts increased. """

    def increase(self):
        self.list_counts.append(int(datetime.datetime.now().strftime("%s")))
        self.update_counter()

    def update_counter(self):
        current_time = int(datetime.datetime.now().strftime("%s"))

        deletions = 0
        for time_stamp in self.list_counts:
            if time_stamp + self.count_timeout < current_time:
                deletions += 1
            else:
                break
        self.list_counts = self.list_counts[deletions:]

    def get_count(self):
        self.update_counter()
        return len(self.list_counts)

    def __init__(self, count_timeout=60):
        self.list_counts = list()
        self.count_timeout = count_timeout


class HandlerSensors(BaseHTTPRequestHandler):

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(self):
        try:
            path_split = self.path.split('/')
            self.do_HEAD()

            request_counter.increase()     # Increase counter on every request

            if path_split[1] == 'get_data':

                reply_data = "".join(choice(string.ascii_letters + string.punctuation) for x in range(0, 100))
                data = json.dumps(reply_data)
                self.wfile.write(data.encode())

            #size = int(self.path.split('/')[1])
            #print ('Starting GET request')

            #self.send_response(200)
            #self.end_headers()
            #payload = os.urandom(size)
            #self.wfile.write(payload)
        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)
        except ValueError:
            self.send_error(404, 'Page Not Found: %s' % self.path)


class HandlerControl(BaseHTTPRequestHandler):

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(self):
        try:
            path_split = self.path.split('/')

            self.do_HEAD()

            if path_split[1] == 'connections':
                count = request_counter.get_count()
                data = json.dumps({"connections": count})
                self.wfile.write(data.encode())

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)
        except ValueError:
            self.send_error(404, 'Page Not Found: %s' % self.path)


class ThreadedHTTPServer(ThreadPoolMixIn, HTTPServer):
    pass


def start_sensors_server():
    """ Starts sensors HTTP server """
    server_sensors = ThreadedHTTPServer(('', 80), HandlerSensors)
    try:
        server_sensors.serve_forever()
    except KeyboardInterrupt:
        pass
    server_sensors.server_close()


if __name__ == '__main__':
    request_counter = RequestCounter(count_timeout=60)

    server_control = ThreadedHTTPServer(('', 8080), HandlerControl)
    print ('Starting server, use <Ctrl-C> to stop')

    thread_server_sensors = Thread(target=start_sensors_server)
    thread_server_sensors.setDaemon(1)
    thread_server_sensors.start()

    server_control.serve_forever()

    thread_server_sensors.join()
    thread_server_sensors.server_close()
