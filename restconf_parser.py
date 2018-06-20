import requests
from lxml import etree
from requests.auth import HTTPBasicAuth


odl_ns = {'i': 'urn:opendaylight:inventory', 'f': 'urn:opendaylight:flow:inventory',
          't': 'urn:TBD:params:xml:ns:yang:network-topology', 'o': 'urn:opendaylight:params:xml:ns:yang:ovsdb',
          's': 'urn:opendaylight:flow:statistics'}


def get_virtual_machines_data_statistics(mac_address):
    """ Returns send/received bytes and packets counts in dictionary for <mac_address> """
    nodes = request_tree(url='http://130.234.169.76:8181/restconf/operational/opendaylight-inventory:nodes', username='admin', psw='admin')
    vm_data_stats = {"sent-packet-count" : 0, "sent-byte-count": 0, "received-packet-count": 0, "received-byte-count": 0}

    # - Flows with <mac_address> as ethernet-source
    source_flows = xpath_query(nodes, '//f:flow[./f:match/f:ethernet-match/f:ethernet-source/f:address = "' + mac_address + '"]')

    for sf in source_flows:
        vm_data_stats["sent-packet-count"] += int(xpath_query(sf, './s:flow-statistics/s:packet-count')[0].text)
        vm_data_stats["sent-byte-count"] += int(xpath_query(sf, './s:flow-statistics/s:byte-count')[0].text)

    # - Flows with <mac_address> as ethernet-destination
    destination_flows = xpath_query(nodes, '//f:flow[./f:match/f:ethernet-match/f:ethernet-destination/f:address = "' + mac_address + '"]')

    for df in destination_flows:
        vm_data_stats["received-packet-count"] += int(xpath_query(sf, './s:flow-statistics/s:packet-count')[0].text)
        vm_data_stats["received-byte-count"] += int(xpath_query(sf, './s:flow-statistics/s:byte-count')[0].text)

    return vm_data_stats


def request_tree(url, username, psw):
    """ Returns etree from url """
    tree_req = requests.get(url,
                            auth=HTTPBasicAuth(username, psw),
                            headers={'Accept': 'text/xml'}, stream=True)
    tree_req.raw.decode_content = True
    return etree.parse(tree_req.raw)


def xpath_query(tree, query):
    """ Uses 'default' namespaces to wrap xpath query """
    global odl_ns
    return tree.xpath(query, namespaces=odl_ns)


def get_virtual_machines_info():
    """ Returns ip, mac, floating ip, connected swtich id, ofport, ofport's mac for all VMs """
    nodes = request_tree(url='http://130.234.169.76:8181/restconf/operational/opendaylight-inventory:nodes', username='admin', psw='admin')
    topology = request_tree(url='http://130.234.169.76:8181/restconf/operational/network-topology:network-topology', username='admin', psw='admin')

    # Queries to extract:
    # - IP and MAC address pair from matches
    ip_mac_pairs = xpath_query(nodes, '//f:match[./f:ipv4-source and ././f:ethernet-match/f:ethernet-source/f:address]')

    virtual_machines = list()

    for ip_mac_pair in ip_mac_pairs:
        ip_address = xpath_query(ip_mac_pair, './f:ipv4-source')[0].text
        mac_address = xpath_query(ip_mac_pair, './f:ethernet-match/f:ethernet-source/f:address')[0].text
        switch_id = xpath_query(ip_mac_pair, './ancestor::i:node/i:id')[0].text

        # Find floating IP:
        # - IP and floating IP pair from matches
        floating_ip_node = xpath_query(nodes, '//f:match[./f:ipv4-source = "' + ip_address + '" and .././f:instructions/f:instruction/f:apply-actions/f:action/f:set-field/f:ipv4-source]')
        floating_ip_address = xpath_query(floating_ip_node[0], '../f:instructions/f:instruction/f:apply-actions/f:action/f:set-field/f:ipv4-source')[0].text

        # Find switch info
        # - MAC address and Switch Info pair from termination points external ids
        switch_info_node = xpath_query(topology, '//o:external-id-value[. = "' + mac_address + '"]')
        ofport = xpath_query(switch_info_node[0], './ancestor::t:termination-point/o:ofport')[0].text
        mac_in_use = xpath_query(switch_info_node[0], './ancestor::t:termination-point/o:mac-in-use')[0].text

        virtual_machines.append({'IP': ip_address.split('/')[0], 'floating_IP': floating_ip_address.split('/')[0], 'MAC': mac_address, 'switch_id': switch_id, 'ofport': ofport, 'ofport_MAC': mac_in_use})

    return virtual_machines


if __name__ == '__main__':

    virtual_machines_info = get_virtual_machines_info()
    for vm in virtual_machines_info:
        statistics = get_virtual_machines_data_statistics(vm['MAC'])
        print("IP:", vm['IP'], "MAC: ", vm['MAC'], statistics)
    print(virtual_machines_info)
    i = 0
