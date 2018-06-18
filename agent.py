import sys, paramiko, threading, json, time
from scp import SCPClient
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

#hostnames = ['192.168.56.11', '192.168.56.24']  # Sensor IPs
#stop_flag = False  # Maybe to use in future?

class Server(BaseHTTPRequestHandler):

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_POST(self):
        """Respond to a POST request."""
        self.do_HEAD()
        if self.path.endswith('update_sensors'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            try:
                sensors = data["sensors"]
                override_text_file("sensors.txt", sensors)

            except KeyError:
                pass
        elif self.path.endswith('update_servers'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            try:
                sensors = data["servers"]
                override_text_file("servers.txt", sensors)

            except KeyError:
                pass

    def do_GET(self):
        """Respond to a GET request."""
        self.do_HEAD()


def start_http_server():
    """" Starts HTTP server """
    global http_server
    http_server = HTTPServer(('', 8080), Server)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    http_server.server_close()


def create_SSH_connection(hostname, port, username, password):
    """ Creates SSH connection. If success returns client, else None """
    try:
        client = paramiko.SSHClient()
        #client.load_system_host_keys()
        #client.set_missing_host_key_policy(paramiko.WarningPolicy)
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=port, username=username, password=password)
        return client
    except Exception as e:
	print e
        return None


def send_file_through_SSH(file_name, client):
    """ Send file through SSH connection using scp """
    scp = SCPClient(client.get_transport())
    scp.put(file_name)


def append_line_to_text_file(file_name, text):
    """ Appends .txt file by one line. """
    text_file = open(file_name, 'a+')
    text_file.write(str(text) + '\n')
    text_file.close()

    
def override_text_file(file_name, lines):
    """ Override .txt file """
    text_file = open(file_name, 'w')
    for line in lines:
        text_file.write(str(line) + '\n')
    text_file.close()


def keep_running(interval):
    	""" Start timer that every <interval> seconds, will take SSH connection to sensors
        and transfers servers.txt file. """
    	#global counter
    	#if not stop_flag:
        	#threading.Timer(30.0, keep_running).start()
    	try:
    		while True:
			try:
				with open('sensors.txt','r') as f:
					lines = f.readlines()
	    			for line in lines:
					host = line.strip()
				        client = create_SSH_connection(host, 22, 'ubuntu', 'ubuntu')
			        	if client:
			            		send_file_through_SSH('servers.txt', client)
			        	client.close()
			except:
				print("File 'sensors.txt is missing")
			time.sleep(interval)			
	except KeyboardInterrupt:
    		pass



if __name__ == '__main__':

    thread_http = Thread(target=start_http_server)
    thread_http.setDaemon(1)
    thread_http.start()
<<<<<<< HEAD
    keep_running(30)
=======
    thread_http.setDaemon(1)
    keep_running()
>>>>>>> 1e96912668328b6b20051d9bf3a156fb1ced9a81

    #thread_http.join()
    #http_server.server_close()
