import os, threading, socket, json

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
from Queue import Queue
from time import time
from datetime import datetime
from subprocess import call

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
	
	def get_alerts(self,ip,port,time_interval):
		dt_now = datetime.now()
		alerts = {"alerts":[]}
		ips = next(os.walk('/var/log/snort'))[1]	
		if ip in ips:
			ip_file_path = '/var/log/snort/'+ip + '/'
			alert_files = [f for f in os.listdir(ip_file_path) if os.path.isfile(ip_file_path + f) and f.split('-')[-1]==port]
			if alert_files:
				for alert_file in alert_files:
					with open(ip_file_path + alert_file,'r') as f:
						lines = f.readlines()
					for i in range(len(lines)):
						line = lines[i]
						title = line.strip()
						if title.startswith('[**]') and title.endswith('[**]'):
							potential_alert = {"message":title[5:-5], "timestamp":"", "src_ip":"", "src_port":"", "dst_ip":"", "dst_port":""}
							try:
								next_line = lines[i+1].strip()
								next_line_items = next_line.split(' ')
								timestamp = datetime.strptime(str(dt_now.year)+'/'+next_line_items[0],'%Y/%m/%d-%H:%M:%S.%f')
								potential_alert['src_ip'] = next_line_items[1].split(':')[0]
								potential_alert['src_port'] = next_line_items[1].split(':')[1]
								potential_alert['dst_ip'] = next_line_items[3].split(':')[0]
								potential_alert['dst_port'] = next_line_items[3].split(':')[1]	
								if (datetime.now() - timestamp).total_seconds < time_interval:
									potential_alert['timestamp'] = str(timestamp)
									alerts["alerts"].append(potential_alert)
							except Exception, e:
								print e
		return alerts

	def get_rules(self):
		with open('/etc/snort/rules/local.rules','r') as f:
			lines = f.readlines()
		rules = {"rules": []}
		for line in lines:
			if line.startswith('alert'):
				rules['rules'].append(line.strip())
							
				
		return rules
	
	def update_rules(self,rules)
		with open('/etc/snort/rules/local.rules','w') as f:
			for rule in rules['rules']:
				f.write(rule + '\n')
							
		return 0

	def do_GET(self):
        	try:
			path_items = self.path.split('/')
			if path_items[1] == 'get_alerts':
	            		ip = path_items[2]
        	    		port = path_items[3]
	            		time_interval = path_items[4]
				alerts = self.get_alerts(ip,port,time_interval)
            			self.send_response(200)
            			self.end_headers()
				data = json.dumps(alerts)
			        self.wfile.write(data.encode())

			elif path_items[1] == 'get_rules':
            			self.send_response(200)
            			self.end_headers()
				rules = self.get_rules()
				data = json.dumps(rules)
			        self.wfile.write(data.encode())
			
        	except IOError:
            		self.send_error(404,'File Not Found: %s' % self.path)
	
	def do_POST(self):
		try:
			path_items = self.path.split('/')
			if path_items[1] == 'update_rules':
				content_length = int(self.headers['Content-Length'])
		            	post_data = self.rfile.read(content_length)
        		    	rules = json.loads(post_data)
				update_rules(rules)
        	except IOError:
            		self.send_error(404,'File Not Found: %s' % self.path)
		

class ThreadedHTTPServer(ThreadPoolMixIn, HTTPServer):
    pass

def start_snort():
	print('Starting snort!')
	call(['snort','-d','-K','ascii'])

if __name__ == '__main__':

	t = threading.Thread(target = start_snort)
        t.setDaemon(1)
        t.start()

	print ('Starting server, use <Ctrl-C> to stop')
	server = ThreadedHTTPServer(('', 8080), Handler)
	server.serve_forever()

