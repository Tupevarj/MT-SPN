
import re
import threading
import random
import requests
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import json

stop_flag = False  # Maybe to use in future?

def parse_text_file(file_name, regex):
    """ Parses .txt file. Returns list of elements, that
        match regular expression """
    text_file = open(file_name, 'r')
    parsed = list()

    while True:
        line = text_file.readline()
        if not line:
            break
        parsed.extend(re.split(regex, line.rstrip('\n')))
    text_file.close()
    return parsed


def append_line_to_text_file(file_name, text):
    """ Appends .txt file by one line. """
    text_file = open(file_name, 'a+')
    text_file.write(str(text) + '\n')
    text_file.close()


def pick_random(choices):
    """ Return random element from list """
    return random.choice(choices)


class Server(BaseHTTPRequestHandler):

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(self):
        """Respond to a GET request."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        parsed_log = parse_text_file('log.txt', '')
        data = json.dumps({'data': parsed_log})
        self.wfile.write(data.encode())


def start_http_server():
    """" Starts HTTP server """
    global http_server
    http_server = HTTPServer(('', 8080), Server)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    http_server.server_close()
    

def send_get_request(address):
    """ Sends HTTP request and return JSON parsed reply """
    request = requests.get(address)
    return request.json()


def keep_running():
    """ Keeps sending GET request every 10 seconds to random ip from servers.txt file.
        Reply is stored in payloads.txt"""
    if not stop_flag:
        threading.Timer(10.0, keep_running).start()
    random_ip = pick_random(parse_text_file('./servers.txt', ' '))
    #parsed = send_get_request('http://' + random_ip + ':8080')  # Just to test http server (127.0.0.1 in servers.txt)
    parsed = send_get_request('http://' + random_ip + '/get_data')
    append_line_to_text_file('payloads.txt', parsed['data'])


if __name__ == "__main__":
    # Start running
    thread_http = Thread(target=start_http_server)
    thread_http.start()
    keep_running()

    # Clean up:
    thread_http.join()
    http_server.server_close()
