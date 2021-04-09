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
    ly = config.layer1.layer1()[-1]
    ly.name = 'ly'
    ly.port_names = [tx.name, rx1.name, rx2.name]
    ly.ieee_media_defaults = False
    ly.auto_negotiate = False
    ly.speed = utils.settings.speed
    ly.media = utils.settings.media

    tx_device, rx1_device, rx2_device = (
        config.devices
        .device(name="tx_device", container_name=tx.name)
        .device(name="rx1_device", container_name=rx1.name)
        .device(name="rx2_device", container_name=rx2.name)
    )

    # TODO: DUT interfaces configuration..
    # ..should be imported from external settings

    # tx_device config
    tx_eth = tx_device.ethernet
    tx_eth.name = "tx_eth"
    tx_ipv4 = tx_eth.ipv4
    tx_ipv4.name = "tx_ipv4"
    tx_ipv4.address = "21.1.1.2"
    tx_ipv4.prefix = "24"
    tx_ipv4.gateway = "21.1.1.1"

    # rx1_device config
    rx1_eth = rx1_device.ethernet
    rx1_eth.name = "rx1_eth"
    rx1_ipv4 = rx1_eth.ipv4
    rx1_ipv4.name = "rx1_ipv4"
    rx1_ipv4.address = "22.1.1.2"
    rx1_ipv4.prefix = "24"
    rx1_ipv4.gateway = "22.1.1.1"
    rx1_bgpv4 = rx1_ipv4.bgpv4
    rx1_bgpv4.name = "rx1_bgpv4"
    rx1_bgpv4.as_type = "ebgp"
    rx1_bgpv4.dut_address = "22.1.1.1"
    rx1_bgpv4.as_number = "65200"
    rx1_rr = rx1_bgpv4.bgpv4_routes.bgpv4route()[-1]
    rx1_rr.name = "rx1_rr"
    # rx1_rr.address_count = "1000"
    # rx1_rr.address = "200.1.0.1"
    # rx1_rr.prefix = "32"

    # rx2_device config
    rx2_eth = rx2_device.ethernet
    rx2_eth.name = "rx2_eth"
    rx2_ipv4 = rx2_eth.ipv4
    rx2_ipv4.name = "rx2_ipv4"
    rx2_ipv4.address = "23.1.1.2"
    rx2_ipv4.prefix = "24"
    rx2_ipv4.gateway = "23.1.1.1"
    rx2_bgpv4 = rx2_ipv4.bgpv4
    rx2_bgpv4.name = "rx2_bgp"
    rx2_bgpv4.as_type = "ebgp"
    rx2_bgpv4.dut_address = "23.1.1.1"
    rx2_bgpv4.as_number = "65200"

    rx2_rr = rx2_bgpv4.bgpv4_routes.bgpv4route()[-1]
    rx2_rr.name = "rx2_rr"
    # rx2_rr.address_count = "1000"
    # rx2_rr.address = "200.1.0.1"
    # rx2_rr.prefix = "32"

    # flow config
    flow = config.flows.flow(name='convergence_test')[-1]
    flow.tx_rx.device.tx_names = [tx_device.name]
    flow.tx_rx.device.rx_names = [rx1_rr.name, rx2_rr.name]

    flow.size.fixed = "1024"
    flow.rate.percentage = "50"

    return config
