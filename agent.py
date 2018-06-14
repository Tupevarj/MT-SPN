import sys, paramiko
import threading
from scp import SCPClient

hostnames = ['192.168.56.11', '192.168.56.24']  # Sensor IPs
stop_flag = False  # Maybe to use in future?
# counter = 0  # For testing ONLY!

def create_SSH_connection(hostname, port, username, password):
    """ Creates SSH connection. If success returns client, else None """
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy)

        client.connect(hostname, port=port, username=username, password=password)
        return client
    except:
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

def keep_running():
    """ Start timer that every 30 seconds, will take SSH connection to sensors
        and transfers servers.txt file. """
    global counter
    if not stop_flag:
        threading.Timer(30.0, keep_running).start()
    for host in hostnames:
        client = create_SSH_connection(host, 22, 'ubuntu', 'ubuntu')
        if not (client is None):
            # counter += 1
            # append_line_to_text_file('servers.txt', str(counter))  # For testing ONLY!
            send_file_through_SSH('servers.txt', client)
        client.close()

if __name__ == '__main__':
    keep_running()
