from odl_restconf_requests import Operational


class FlowMonitor:

    def __init__(self):
        self.op = Operational('130.234.169.76', 8181, 'admin', 'admin')
        self.vm_cache = dict()
        self.traffic_cache = dict()

    def update_vm_list(self):
        """ Updates VM ip and floating ip addresses cache. """
        vms = self.op.get_vms()
        for vm in vms:
            if vm['mac'] not in self.vm_cache:
                self.vm_cache[vm['mac']] = {'ip': vm['ip'], 'floating_ip': vm['floating_ip']}

    @staticmethod
    def change_in_traffic(previous, current):
        """ Calculates change in to data traffic dictionaries. """
        return {'ip': current['ip'], 'sent_packets': current['sent_packets'] - previous['sent_packets'], 'sent_bytes':
                current['sent_bytes'] - previous['sent_bytes'], 'received_packets': current['received_packets'] -
                previous['received_packets'], 'received_bytes': current['received_bytes'] - previous['received_bytes']}

    @staticmethod
    def empty_traffic(ip_address):
        """ Initializes empty data traffic dictionary using <ip_address>. """
        return {'ip': ip_address, 'sent_packets': 0, 'sent_bytes': 0, 'received_packets': 0, 'received_bytes': 0 }

    def get_traffic(self, mac_address):
        """ Gets data traffic for <mac_address>. """
        if mac_address not in self.vm_cache:
            self.update_vm_list()

        try:
            floating_ip = self.vm_cache[mac_address]['floating_ip']
            ip = self.vm_cache[mac_address]['ip']
        except KeyError:
            print("Error, MAC address not recognized!")
            return

        internal_traffic = self.op.get_internal_traffic_count(mac_address, ip)
        external_traffic = self.op.get_external_traffic_count(floating_ip)

        # Subtract external source traffic from internal source traffic:
        internal_traffic['sent_bytes'] = internal_traffic['sent_bytes'] - external_traffic['sent_bytes']
        internal_traffic['sent_packets'] = internal_traffic['sent_packets'] - external_traffic['sent_packets']

        if mac_address in self.traffic_cache:
            change_internal = self.change_in_traffic(self.traffic_cache[mac_address]['internal'], internal_traffic)
            change_external = self.change_in_traffic(self.traffic_cache[mac_address]['external'], external_traffic)
        else:
            change_internal = self.empty_traffic(ip)
            change_external = self.empty_traffic(floating_ip)

        self.traffic_cache[mac_address]['internal'] = internal_traffic
        self.traffic_cache[mac_address]['external'] = external_traffic
        
        return {'internal': change_internal, 'external': change_external}
        
