import pytest

@pytest.mark.non_uhd
def test_vxlan(api, utils):
    config = api.config()

    p1, p2 = config.ports.port(
        name="tx", location=utils.settings.ports[0]
    ).port(name="rx", location=utils.settings.ports[1])

    d1, d2 = config.devices.device(name="d1").device(name="d2")

    e1, e2 = d1.ethernets.ethernet()[-1], d2.ethernets.ethernet()[-1]
    e1.port_name, e2.port_name = p1.name, p2.name
    e1.name, e2.name = "e1", "e2"
    e1.mac, e2.mac = "00:01:00:00:00:01", "00:01:00:00:00:02"

    ip1, ip2 = e1.ipv4_addresses.add(), e2.ipv4_addresses.add()
    ip1.name, ip2.name = "ip_d1", "ip_d2"

    ip1.address, ip2.address = "10.10.10.1", "10.10.10.2"
    ip1.gateway, ip2.gateway = "10.10.10.2", "10.10.10.1"

    # Create vxlan on d1
    d1_vxlan = d1.vxlan.v4_tunnels.add()

    d1_vxlan.vni = 1000
    d1_vxlan.source_interface = ip1.name
    d1_vxlan.name = "d1_vxlan"

    # multicast communication
    d1_vxlan.destination_ip_mode.multicast.address = "225.0.0.1"

    # Create vxlan on d2
    d2_vxlan = d2.vxlan.v4_tunnels.add()

    d2_vxlan.vni = 1000
    d2_vxlan.source_interface = ip2.name
    d2_vxlan.name = "d2_vxlan"

    # multicast communication
    d2_vxlan.destination_ip_mode.multicast.address = "225.0.0.1"

    # create two edge devices to communicate over vxlan
    edge_d1 = config.devices.device(name="edge_d1")[-1]
    edge_d2 = config.devices.device(name="edge_d2")[-1]

    edge_e1 = edge_d1.ethernets.ethernet()[-1]
    edge_e2 = edge_d2.ethernets.ethernet()[-1]

    edge_e1.connection.vxlan_name = d1_vxlan.name
    edge_e2.connection.vxlan_name = d2_vxlan.name

    edge_e1.name, edge_e2.name = "edge_e1", "edge_e2"
    edge_e1.mac, edge_e2.mac = "00:18:01:00:00:01", "00:16:01:00:00:01"

    edge_ip1 = edge_e1.ipv4_addresses.add()
    edge_ip2 = edge_e2.ipv4_addresses.add()

    edge_ip1.name, edge_ip2.name = "edge_ip_d1", "edge_ip_d2"

    edge_ip1.address, edge_ip2.address = "100.1.1.1", "100.1.1.2"
    edge_ip1.gateway, edge_ip2.gateway = "100.1.1.2", "100.1.1.1"

    edge_bgp1, edge_bgp2 = edge_d1.bgp, edge_d2.bgp
    edge_bgp1.router_id, edge_bgp2.router_id = "100.1.1.1", "100.1.1.2"

    edge_bgp1_ipv4 = edge_bgp1.ipv4_interfaces.add()
    edge_bgp2_ipv4 = edge_bgp2.ipv4_interfaces.add()

    edge_bgp1_ipv4.ipv4_name = edge_ip1.name
    edge_bgp2_ipv4.ipv4_name = edge_ip2.name

    edge_bgp1_peer = edge_bgp1_ipv4.peers.add()
    edge_bgp2_peer = edge_bgp2_ipv4.peers.add()

    edge_bgp1_peer.name, edge_bgp2_peer.name = "edge_bgp1", "edge_bgp2"

    edge_bgp1_peer.peer_address = "100.1.1.2"
    edge_bgp2_peer.peer_address = "100.1.1.1"

    edge_bgp1_peer.as_type, edge_bgp2_peer.as_type = "ibgp", "ibgp"
    edge_bgp1_peer.as_number, edge_bgp2_peer.as_number = 1000, 1000

    # api.set_config(config)
    edge_bgp1_rr = edge_bgp1_peer.v4_routes.add(name="A1")
    edge_bgp1_rr.addresses.add(address="200.1.1.1", prefix=32)

    edge_bgp2_rr = edge_bgp2_peer.v4_routes.add(name="A2")
    edge_bgp2_rr.addresses.add(address="201.1.1.1", prefix=32)

    flow = config.flows.flow(name="f1")[-1]
    flow.tx_rx.device.tx_names = [edge_bgp1_rr.name]
    flow.tx_rx.device.rx_names = [edge_bgp2_rr.name]

    flow.duration.fixed_packets.packets = 100

    flow.metrics.enable = True
    flow.metrics.loss = True

    utils.start_traffic(api, config, start_capture=False)

    utils.wait_for(
        lambda: results_ok(api, ["f1"], 100),
        "stats to be as expected",
        timeout_seconds=10,
    )
    utils.stop_traffic(api, config)


def results_ok(api, flow_names, expected):
    """
    Returns True if there is no traffic loss else False
    """
    request = api.metrics_request()
    request.flow.flow_names = flow_names
    flow_results = api.get_metrics(request).flow_metrics
    flow_rx = sum([f.frames_rx for f in flow_results])
    return flow_rx == expected


if __name__ == "__main__":
    pytest.main(["-s", __file__])
