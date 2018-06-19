import requests, json

agent = ['192.168.56.28']
cc = ['192.168.56.30']
sensors = ['192.168.56.24', '192.168.56.11']
compromised_sensors = ['192.168.56.11']
http_servers = ['192.168.56.13', '192.168.56.15']


# IPs of all instances
instance_ips = {'agent': agent, 'cc': cc, 'sensors': sensors, 'http_servers': http_servers}

# Scenario
scenario = [

	# config!
	{'message': "Checking instance statuses", 'function': "check_all_instance_statuses()"},

	# action!
	{'message': "Checking sensors for infection", 'function': "check_sensors_for_infection()"},
	{'message': "Checking cc for zombies", 'function': "check_cc_zombies()"},
	{'message': "Starting devices infection", 'function': "start_device_infection()"},
	{'message': "Checking sensors for infection", 'function': "check_sensors_for_infection()"},
	{'message': "Checking cc for zombies", 'function': "check_cc_zombies()"},
	{'message': "Checking HTTP server connections", 'function': "check_http_connections()"},
	{'message': "Starting DDoS attack", 'function': "start_ddos_attack()"},
	{'message': "Checking HTTP server connections", 'function': "check_http_connections()"},

	# reset!
	{'message': "Stopping DDoS attack", 'function': "stop_ddos_attack()"},
	{'message': "Checking HTTP server connections", 'function': "check_http_connections()"},
	{'message': "Removing malware from zombie sensors", 'function': "clean_zombie_sensors()"},
	{'message': "Checking sensors for infection", 'function': "check_sensors_for_infection()"},
	{'message': "Checking cc for zombies", 'function': "check_cc_zombies()"},

]

def test_connection_status(address, timeout):
    """ Checks HTTP request and return boolean """
    try:
        requests.get(address, timeout=timeout)
        return True
    except:  # Exception as e:
        return False


def check_instance_status(ip):
    """ Test connection to specific IP on port 8080"""
    if test_connection_status('http://' + ip + ':8080', 4):
	status = 'READY'
    else:
	status = 'NOT READY'
    return status

def configure_sensor_agent():
	payload_sensors = {"sensors": []}
	for sensor in sensors:
		payload_sensors['sensors'].append(sensor)
	payload_servers = {"servers": []}
	for server in http_servers:
		payload_servers['servers'].append(server)
	try:
		update_sensors_url = 'http://' + agent[0] + ':8080/update_sensors'
		r = requests.post(update_sensors_url,data=json.dumps(payload_sensors))
		update_servers_url = 'http://' + agent[0] + ':8080/update_servers'
		r = requests.post(update_servers_url,data=json.dumps(payload_servers))
		print('Agent has been configurred!')
	except Exception as e:
        	print e

def configure_zombie_cc():
	payload_bots = {"bots": []}
	for bot in compromised_sensors:
		payload_bots['bots'].append(bot)
	try:
		update_bots_url = 'http://' + cc[0] + ':8080/bots'
		r = requests.post(update_bots_url,data=json.dumps(payload_bots))
		print('CC has been configurred!')
	except Exception as e:
        	print e

def check_all_instance_statuses():
    """ Goes through all the IPs and check their connection """
    for key, value in instance_ips.items():
        print('\n' + key + ':')
        for ip in value:
            status = check_instance_status(ip)
            print(ip + ' is ' + status)
    print('\n')
    configure_sensor_agent()
    configure_zombie_cc()

def check_sensors_for_infection():
	for sensor in sensors:
		try:
			address = 'http://' + sensor + ':8080/status'
			r = requests.get(address)
			status = json.loads(r.text)
        		print('Sensor ' + sensor + ' reports: ' + status['status'])
    		except Exception as e:
        		print e

def check_cc_zombies():
	try:
		request_zombies_url = 'http://' + cc[0] + ':8080/zombies'
		r = requests.get(request_zombies_url)
		zombies = json.loads(r.text)
		for zombie in zombies['zombies']:
			print zombie['ip'], zombie['command']
	except Exception as e:
        	print e

def start_ssh_scan(): # not used
	payload_commands = {"commands": {"command":"scan"}}
	try:
		update_commands_url = 'http://' + cc[0] + ':8080/commands'
		r = requests.post(update_commands_url,data=json.dumps(payload_commands))
		print('Scanning sensors subnet!')
	except Exception as e:
        	print e

def start_device_infection():
	payload_commands = {"commands": {"command":"infect"}}
	try:
		update_commands_url = 'http://' + cc[0] + ':8080/commands'
		r = requests.post(update_commands_url,data=json.dumps(payload_commands))
		print('Infecting other sensors!')
	except Exception as e:
        	print e

def check_http_connections():
	for server in http_servers:
		try:
			address = 'http://' + server + ':8080/connections'
			r = requests.get(address)
			connections = json.loads(r.text)
        		print('Web server ' + server + ' load: %0.2f connections per minute' % connections['connections'])
    		except Exception as e:
        		print e

def start_ddos_attack(target=http_servers[1]):
	payload_commands = {"commands": {"command":"ddos", "target":target, "uri":"get_data"}}
	try:

		update_commands_url = 'http://' + cc[0] + ':8080/commands'
		r = requests.post(update_commands_url,data=json.dumps(payload_commands))
		print('Starting DDoS attack against ' + target + '!')
	except Exception as e:
        	print e

def stop_ddos_attack():
	payload_commands = {"commands": {"command":"stop"}}
	try:
		update_commands_url = 'http://' + cc[0] + ':8080/commands'
		r = requests.post(update_commands_url,data=json.dumps(payload_commands))
		print('Stopping the DDoS attack!')
	except Exception as e:
        	print e

def clean_zombie_sensors():
	for sensor in sensors:
		if sensor not in compromised_sensors:
			try:
				address = 'http://' + sensor + ':8080/reset'
				r = requests.get(address)
	        		print('Sensor ' + sensor + ' has been cleaned!')
	    		except Exception as e:
        			print e

def execute_scenario():
	for step in scenario:
		try:
			raw_input("\nPress any key to continue...\n")
		except KeyboardInterrupt:
			print "Cancelled"
		print('\n*** ' + step['message'] + ' ***\n')
		exec(step['function'])

if __name__ == '__main__':
    execute_scenario()

