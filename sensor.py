
import re
import threading
import random
import requests
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import json
from pathlib import Path
import time
import datetime
import os

stop_flag = False


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

        path_split = self.path.split('/')

        if path_split[1] == 'status':
            reply = 'i_am_good"'
            malware_file = Path("/home/ubuntu/malware.py")
            if malware_file.is_file():
                reply = 'i_am_infected'
            self.append_log(reply)
            self.wfile.write(json.dumps(reply).encode())

        elif path_split[1] == 'reset':
            malware_file = Path("/home/ubuntu/malware.py")
            if malware_file.is_file():
                os.remove("/home/ubuntu/malware.py")

        self.do_HEAD()
        #parsed_log = parse_text_file('log.txt', '')
        #data = json.dumps({'data': parsed_log})
        #self.wfile.write(data.encode())

    def append_log(self, message):
        time_stamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        append_line_to_text_file("log.txt", time_stamp + '\t' + message)


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
    try:
        request = requests.get(address + '/get_data')
        return request.json()
    except requests.exceptions.ConnectionError:
        return None


def keep_running():
    """ Keeps sending GET request every 10 seconds to random ip from servers.txt file.
        Reply is stored in payloads.txt"""
    if not stop_flag:
        threading.Timer(10.0, keep_running).start()
    random_ip = pick_random(parse_text_file('./servers.txt', ' '))
    parsed = send_get_request('http://' + random_ip)
    if not (parsed is None):
        append_line_to_text_file('payloads.txt', parsed)


if __name__ == "__main__":

    thread_http = Thread(target=start_http_server)
    thread_http.start()
    keep_running()

    thread_http.join()
    http_server.server_close()
