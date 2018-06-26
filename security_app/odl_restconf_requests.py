import requests,  time
from lxml import etree
from requests.auth import HTTPBasicAuth

class Operational():
    
    ns = {
        't': 'urn:TBD:params:xml:ns:yang:network-topology', 
        'o': 'urn:opendaylight:params:xml:ns:yang:ovsdb', 
        'n': 'urn:opendaylight:inventory', 
        'f': 'urn:opendaylight:flow:inventory', 
    }
        
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

if __name__ == '__main__':
    op = Operational('130.234.169.76',8181,'admin','admin')
    tunnels = op.get_tunnels()
    for tunnel in tunnels:
        print(tunnel)
    vms = op.get_vms()
    for vm in vms:
        print(vm)
