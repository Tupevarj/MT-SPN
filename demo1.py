import requests

agent = '192.168.56.28'
cc = '192.168.56.30'
sensors = ['192.168.56.24', '192.168.56.11']
compromised_sensors = ['192.168.56.11']
http_servers = ['192.168.56.13', '192.168.56.15']


# IPs of all instances
instance_ips = {'agent': [agent], 'cc': [cc], 'sensors': sensors, 'http_servers': http_servers}


def test_connection_status(address, timeout):
    """ Checks HTTP request and return boolean """
    try:
        requests.get(address, timeout=timeout)
        return True
    except:  # Exception as e:
        return False


def check_instance_status(ip):
    """ Test connection to specific IP on port 8080"""
    if test_connection_status('http://' + ip + ':8080', 1):
        print(ip + ' status = READY')
    else:
        print(ip + ' status = CONNECTION FAILED')


def check_all_instance_statuses():
    """ Goes through all the IPs and check their connection """
    for key, value in instance_ips.items():
        print('\n' + key + ':')
        for ip in value:
            check_instance_status(ip)


if __name__ == '__main__':
    check_all_instance_statuses()
