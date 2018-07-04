from odl_restconf_requests import Operational
import threading

class FlowMonitor:

    def __init__(self):
        self.op = Operational('130.234.169.76', 8181, 'admin', 'admin')
        self.vm_cache = dict()
        self.traffic_cache = dict()
        self.m_running = False

    def update_vm_list(self):
        """ Updates VM ip and floating ip addresses cache. """
        vms = self.op.get_vms()
        for vm in vms:
            if vm['mac'] not in self.vm_cache:
                self.vm_cache[vm['mac']] = {'ip': vm['ip'], 'floating_ip': vm['floating_ip']}

    @staticmethod
    def change_in_traffic(previous, current, divider=1):
        """ Calculates change in to data traffic dictionaries. """
        return {'ip': current['ip'], 'sent_packets': (current['sent_packets'] - previous['sent_packets']) / divider, 'sent_bytes':
            (current['sent_bytes'] - previous['sent_bytes']) / divider, 'received_packets': (current['received_packets'] -
                previous['received_packets']) / divider, 'received_bytes': (current['received_bytes'] - previous['received_bytes']) / divider}

    @staticmethod
    def empty_traffic(ip_address):
        """ Initializes empty data traffic dictionary using <ip_address>. """
        return {'ip': ip_address, 'sent_packets': 0, 'sent_bytes': 0, 'received_packets': 0, 'received_bytes': 0}

    def print_data_traffic(self):
        rates = self.op.get_traffic_rates()
        for key, value in rates.items():
            print (value)
        print("----------------------------------------------------------------")

    def keep_monitoring(self, interval):
        if self.m_running:
            threading.Timer(interval, self.print_data_traffic, interval).start()
        self.print_data_traffic()

    def start_monitoring(self, interval=5.0):
        self.m_running = True
        self.keep_monitoring(interval)

    def stop_monitoring(self):
        self.m_running = False
