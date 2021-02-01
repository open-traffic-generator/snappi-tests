import pytest


@pytest.fixture
def bgp_convergence_config(api, utils):
    """
    1.Configure IPv4 EBGP sessions between Keysight ports
    2.Advertise IPv4 routes
    3.Configure and advertise same IPv4 routes
    4.Configure another IPv4 session to send the traffic.
    """
    config = api.config()

    tx, rx1, rx2 = (
        config.ports
        .port(name='tx', location=utils.settings.ports[0])
        .port(name='rx1', location=utils.settings.ports[1])
        .port(name='rx2', location=utils.settings.ports[2])
    )

    config.options.port_options.location_preemption = True
    layer1 = config.layer1.layer1()[-1]
    layer1.name = 'port settings'
    layer1.port_names = [tx.name, rx1.name, rx2.name]
    layer1.ieee_media_defaults = False
    layer1.auto_negotiate = False
    layer1.speed = 'speed_100_gbps'

    tx_device, rx1_device, rx2_device = config.devices.\
        device(name="tx-device", container_name=tx.name).\
        device(name="rx1-device", container_name=rx1.name).\
        device(name="rx2-device", container_name=rx2.name)

    # tx_device config
    tx_device.ipv4.name = "tx-ipv4"
    tx_device.ipv4.address.value = "21.1.1.2"
    tx_device.ipv4.prefix.value = "24"
    tx_device.ipv4.gateway.value = "21.1.1.1"

    # rx1_device config
    rx1_device.bgpv4.name = "rx1-bgp"
    rx1_device.bgpv4.as_type = "ebgp"
    rx1_device.bgpv4.dut_ipv4_address.value = "22.1.1.1"
    rx1_device.bgpv4.as_number.value = 65200
    rx1_device.bgpv4.ipv4.name = "rx1-ipv4"
    rx1_device.bgpv4.ipv4.address.value = "22.1.1.2"
    rx1_device.bgpv4.ipv4.prefix.value = "24"
    rx1_device.bgpv4.ipv4.gateway.value = "22.1.1.1"

    rx1_rr = rx1_device.bgpv4.bgpv4_route_ranges.bgpv4routerange()[-1]
    rx1_rr.name = "rx1-routerange"
    rx1_rr.route_count_per_device = 1000
    rx1_rr.address.value = "200.1.0.1"
    rx1_rr.prefix.value = "32"

    # rx2_device config
    rx2_device.bgpv4.name = "rx2-bgp"
    rx2_device.bgpv4.as_type = "ebgp"
    rx2_device.bgpv4.dut_ipv4_address.value = "23.1.1.1"
    rx2_device.bgpv4.as_number.value = 65200
    rx2_device.bgpv4.ipv4.name = "rx2-ipv4"
    rx2_device.bgpv4.ipv4.address.value = "23.1.1.2"
    rx2_device.bgpv4.ipv4.prefix.value = "24"
    rx2_device.bgpv4.ipv4.gateway.value = "23.1.1.1"

    rx2_rr = rx2_device.bgpv4.bgpv4_route_ranges.bgpv4routerange()[-1]
    rx2_rr.name = "rx2-routerange"
    rx2_rr.route_count_per_device = 1000
    rx2_rr.address.value = "200.1.0.1"
    rx2_rr.prefix.value = "32"

    # flow config
    # TODO : Implement rx_names to be names of device names
    # or network group names
    flow = config.flows.flow(name='convergence-test')[-1]
    flow.tx_rx.device.tx_names = [tx_device.name]
    flow.tx_rx.device.rx_names = ["rx1-routerange", "rx2-routerange"]

    flow.size.fixed = 1024
    flow.rate.percentage = 50

    return config
