import requests,  time
from lxml import etree
from requests.auth import HTTPBasicAuth

class Operational():
    
    ns = {
        't': 'urn:TBD:params:xml:ns:yang:network-topology', 
        'o': 'urn:opendaylight:params:xml:ns:yang:ovsdb', 
        'n': 'urn:opendaylight:inventory', 
        'f': 'urn:opendaylight:flow:inventory',
        's': 'urn:opendaylight:flow:statistics'}
        
    xpath = {
        'tp': '//t:topology/t:node/t:termination-point', 
        'tp_port': '/o:ofport/text()', 
        'tp_port_name': '/o:name/text()', 
        'tp_port_mac': '/o:mac-in-use/text()', 

        'vm': '[./o:interface-external-ids/o:external-id-key/text()="vm-id"]', 
        'vm_mac': '/o:interface-external-ids[./o:external-id-key/text()="attached-mac"]/o:external-id-value/text()', 

        'tun': '[./o:name[contains(text(),"tun")]]', 
        'tp_option': '/o:options[./o:option/text()=$opt]/o:value/text()', 
        
        'node_id_by_nc_name': '//n:nodes/n:node[./n:node-connector/f:name/text()=$nc_name]/n:id/text()', 
        'flow': '//n:nodes/n:node/f:table/f:flow', 
        'arp_by_mac': '/f:match[./f:ethernet-match/*[local-name()=$pd]/f:address/text()=$mac]/f:arp-source-transport-address/text()', 
        'snat_by_ip': '[./f:match/*[local-name()=$pd]/text()=$ip]/f:instructions/f:instruction/f:apply-actions/f:action/f:set-field/*[local-name()=$pd]/text()', 
    }
    
    def __init__(self, ip, port, user, password):
        self.odl_ip = ip
        self.odl_port = port
        self.auth=HTTPBasicAuth(user, password)
        self.headers={'Accept':'text/xml'}
        self.ovsdb = 'http://' + ip + ':' + str(port) + '/restconf/operational/network-topology:network-topology/topology/ovsdb:1'
        self.nodes = 'http://' + ip + ':' + str(port) + '/restconf/operational/opendaylight-inventory:nodes'

    def get_xml_root(self, url):
        req = requests.get(url, auth=self.auth, headers=self.headers,  stream=True)        
        req.raw.decode_content = True
        tree = etree.parse(req.raw)
        root = tree.getroot()
        return root 
        
    def get_vms(self):
        vms = []
        # xml tree roots
        ovsdb_root = self.get_xml_root(self.ovsdb)
        nodes_root = self.get_xml_root(self.nodes)
        # find vms among topology termination points
        vm_macs = ovsdb_root.xpath(self.xpath['tp']+self.xpath['vm']+self.xpath['vm_mac'], namespaces=self.ns)
        tp_vm_names = ovsdb_root.xpath(self.xpath['tp']+self.xpath['vm']+self.xpath['tp_port_name'], namespaces=self.ns)
        tp_vm_macs = ovsdb_root.xpath(self.xpath['tp']+self.xpath['vm']+self.xpath['tp_port_mac'], namespaces=self.ns)
        tp_vm_ofports = ovsdb_root.xpath(self.xpath['tp']+self.xpath['vm']+self.xpath['tp_port'], namespaces=self.ns)
        # find vms' ip addresses using flow tables
        for i in range(len(tp_vm_names)):
            node_id = nodes_root.xpath(self.xpath['node_id_by_nc_name'], nc_name=tp_vm_names[i], namespaces=self.ns)[0]
            ip = nodes_root.xpath(self.xpath['flow'] + self.xpath['arp_by_mac'], pd='ethernet-source', mac=vm_macs[i], namespaces=self.ns)[0]
            floating_ip = nodes_root.xpath(self.xpath['flow'] + self.xpath['snat_by_ip'], pd='ipv4-source', ip=ip , namespaces=self.ns)[0]
            vms.append({'mac': vm_macs[i], 'nc': {'name': tp_vm_names[i], 'mac': tp_vm_macs[i],  'node': node_id,  'port': tp_vm_ofports[i]}, 'ip': ip, 'floating_ip': floating_ip})
        return vms

    def get_tunnels(self):
        tunnels = []
        # xml tree roots
        ovsdb_root = self.get_xml_root(self.ovsdb)
        nodes_root = self.get_xml_root(self.nodes)
        # find tunnels among topology termination points
        tp_tun_ports = ovsdb_root.xpath(self.xpath['tp']+self.xpath['tun']+self.xpath['tp_port'], namespaces=self.ns)
        tp_tun_names = ovsdb_root.xpath(self.xpath['tp']+self.xpath['tun']+self.xpath['tp_port_name'], namespaces=self.ns)
        tp_tun_macs = ovsdb_root.xpath(self.xpath['tp']+self.xpath['tun']+self.xpath['tp_port_mac'], namespaces=self.ns)
        tp_tun_local_ips = ovsdb_root.xpath(self.xpath['tp']+self.xpath['tun']+self.xpath['tp_option'], opt='local_ip', namespaces=self.ns)
        tp_tun_remote_ips = ovsdb_root.xpath(self.xpath['tp']+self.xpath['tun']+self.xpath['tp_option'], opt='remote_ip', namespaces=self.ns)
        for i in range(len(tp_tun_names)):
            node_id = nodes_root.xpath(self.xpath['node_id_by_nc_name'], nc_name=tp_tun_names[i], namespaces=self.ns)[0]
            k = [j for j in range(len(tp_tun_names)) if tp_tun_local_ips[i] == tp_tun_remote_ips[j] and tp_tun_remote_ips[i] == tp_tun_local_ips[j]][0]
            remote_node_id = nodes_root.xpath(self.xpath['node_id_by_nc_name'], nc_name=tp_tun_names[k], namespaces=self.ns)[0]
            tunnels.append({'name': tp_tun_names[i], 'mac': tp_tun_macs[i], 'local': { 'node': node_id,  'port': tp_tun_ports[i],  'ip': tp_tun_local_ips[i]},  'remote': {'node': remote_node_id,  'port': tp_tun_ports[k],  'ip': tp_tun_remote_ips[i]}})
        return tunnels
    
    def get_external_traffic_count(self, floating_ip):
        """ Try's to find unique SNAT source/destination flows and gets data traffic based
            on unique SNAT flows. """
        nodes_root = self.get_xml_root(self.nodes)
        # Snat source/destination flows:
        snat_source = nodes_root.xpath(self.xpath['flow'] + '[./f:match/f:ipv4-source/text() = "' + floating_ip + '"]', namespaces=self.ns)[0]
        snat_destination = nodes_root.xpath(self.xpath['flow'] + '[./f:match/f:ipv4-destination/text() = "' + floating_ip + '" and ./f:instructions/f:instruction/f:apply-actions/f:action/f:set-field/f:ipv4-destination/text() and not(./f:instructions/f:instruction/f:apply-actions/f:action/f:set-field/f:ethernet-match)]', namespaces=self.ns)[0]

        return {'ip': floating_ip,
                'sent_packets': int(snat_source.xpath(self.xpath['packet_count'], namespaces=self.ns)[0].text),
                'sent_bytes': int(snat_source.xpath(self.xpath['bytes_count'], namespaces=self.ns)[0].text),
                'received_packets': int(snat_destination.xpath(self.xpath['packet_count'], namespaces=self.ns)[0].text),
                'received_bytes': int(snat_destination.xpath(self.xpath['bytes_count'], namespaces=self.ns)[0].text)}

    def get_highest_priority(self, flows):
        h_prior = -1
        h_index = 0
        for index, flow in enumerate(flows):
            prior = int(flow.xpath('./f:priority', namespaces=self.ns)[0].text)
            if prior > h_prior:
                h_index = index
                h_prior = prior
        return flows[h_index]

    @staticmethod
    def change_in_traffic(previous, current, divider=1):
        """ Calculates change in to data traffic dictionaries. """
        return {'ip': current['ip'], 'sent_packets': (current['sent_packets'] - previous['sent_packets']) / divider,
                'sent_bytes':
                    (current['sent_bytes'] - previous['sent_bytes']) / divider,
                'received_packets': (current['received_packets'] -
                                     previous['received_packets']) / divider,
                'received_bytes': (current['received_bytes'] - previous['received_bytes']) / divider}

    @staticmethod
    def empty_traffic(ip_address):
        """ Initializes empty data traffic dictionary using <ip_address>. """
        return {'ip': ip_address, 'sent_packets': 0, 'sent_bytes': 0, 'received_packets': 0, 'received_bytes': 0}

    def get_internal_traffic_count(self, mac_address, ip_address):
        """ Try's to find unique destination flow and total traffic source flow for local ip address
            and gets data traffic based those flows. """
        nodes_root = self.get_xml_root(self.nodes)

        destination_flows = nodes_root.xpath('//f:flow[./f:match/f:ethernet-match/f:ethernet-destination/f:address = "' + mac_address + '" and ./f:match/f:metadata and not(./f:instructions/f:instruction/f:apply-actions/f:action/f:set-field/f:tunnel)]', namespaces=self.ns)
        source_flows = nodes_root.xpath('//f:flow[./f:match/f:ethernet-match/f:ethernet-source/f:address = "' + mac_address + '" and ./f:match/f:ipv4-source and ./f:match/f:metadata and ./f:instructions/f:instruction/f:go-to-table]', namespaces=self.ns)

        source_flow = source_flows[0]
        destination_flow = destination_flows[0]

        if len(destination_flows) > 1:
            destination_flow = self.get_highest_priority(destination_flows)
        if len(source_flows) > 1:
            source_flow = self.get_highest_priority(source_flows)

        return {'ip': ip_address,
                'sent_packets': int(source_flow.xpath(self.xpath['packet_count'], namespaces=self.ns)[0].text),
                'sent_bytes': int(source_flow.xpath(self.xpath['bytes_count'], namespaces=self.ns)[0].text),
                'received_packets': int(destination_flow.xpath(self.xpath['packet_count'], namespaces=self.ns)[0].text),
                'received_bytes': int( destination_flow.xpath(self.xpath['bytes_count'], namespaces=self.ns)[0].text)}

    def update_vm_list(self):
        """ Updates VM ip and floating ip addresses cache. """
        vms = self.get_vms()
        for vm in vms:
            if vm['mac'] not in self.vm_cache:
                self.vm_cache[vm['mac']] = {'ip': vm['ip'], 'floating_ip': vm['floating_ip']}

    def get_traffic_rate(self, mac_address, floating_ip, ip):
        """ Gets data traffic for <mac_address>. """

        internal_traffic = self.get_internal_traffic_count(mac_address, ip)
        external_traffic = self.get_external_traffic_count(floating_ip)
        current_time_ms = int(round(time.time() * 1000))

        # Subtract external source traffic from internal source traffic:
        internal_traffic['sent_bytes'] = internal_traffic['sent_bytes'] - external_traffic['sent_bytes']
        internal_traffic['sent_packets'] = internal_traffic['sent_packets'] - external_traffic['sent_packets']

        if mac_address in self.traffic_cache:
            elapsed_time_ms = current_time_ms - self.traffic_cache[mac_address]['time_stamp']
            change_internal = self.change_in_traffic(self.traffic_cache[mac_address]['internal'], internal_traffic,
                                                     (elapsed_time_ms / 1000.0))
            change_external = self.change_in_traffic(self.traffic_cache[mac_address]['external'], external_traffic,
                                                     (elapsed_time_ms / 1000.0))
        else:
            change_internal = self.empty_traffic(ip)
            change_external = self.empty_traffic(floating_ip)

        self.traffic_cache[mac_address] = {'internal': internal_traffic, 'external': external_traffic,
                                           'time_stamp': current_time_ms}

        return {'internal': change_internal, 'external': change_external}

    def get_traffic_rates(self):
        if len(self.vm_cache) == 0:
            self.update_vm_list()
        data_rates = dict()
        for mac, vm in self.vm_cache.items():
            data_rates[mac] = self.get_traffic_rate(mac, vm['floating_ip'], vm['ip'])
        return data_rates
    

if __name__ == '__main__':
    op = Operational('130.234.169.76',8181,'admin','admin')
    tunnels = op.get_tunnels()
    for tunnel in tunnels:
        print(tunnel)
    vms = op.get_vms()
    for vm in vms:
        print(vm)
