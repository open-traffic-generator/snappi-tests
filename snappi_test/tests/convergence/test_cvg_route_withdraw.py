import pytest
import snappi_convergence


@pytest.fixture(scope="session")
def cvg_api():
    api = snappi_convergence.api(location="localhost:443", ext="ixnetwork")
    yield api
    if getattr(api, "assistant", None) is not None:
        api.assistant.Session.remove()


@pytest.fixture()
def bgp_convergence_config(utils, cvg_api):
    """
    1.Configure IPv4 EBGP sessions between Keysight ports
    2.Advertise IPv4 routes
    3.Configure and advertise same IPv4 routes
    4.Configure another IPv4 session to send the traffic.
    """

    conv_config = cvg_api.convergence_config()
    config = conv_config.config

    tx, rx1, rx2 = (
        config.ports.port(name="tx", location=utils.settings.ports[0])
        .port(name="rx1", location=utils.settings.ports[1])
        .port(name="rx2", location=utils.settings.ports[2])
    )

    config.options.port_options.location_preemption = True
    ly = config.layer1.layer1()[-1]
    ly.name = "ly"
    ly.port_names = [tx.name, rx1.name, rx2.name]
    ly.ieee_media_defaults = True
    ly.auto_negotiate = False
    ly.speed = utils.settings.speed

    tx_device, rx1_device, rx2_device = (
        config.devices.device(name="tx_device", container_name=tx.name)
        .device(name="rx1_device", container_name=rx1.name)
        .device(name="rx2_device", container_name=rx2.name)
    )

    # tx_device config
    tx_eth = tx_device.ethernet
    tx_eth.name = "tx_eth"
    tx_eth.mac = "00:00:00:00:00:aa"
    tx_ipv4 = tx_eth.ipv4
    tx_ipv4.name = "tx_ipv4"
    tx_ipv4.address = "21.1.1.2"
    tx_ipv4.prefix = 24
    tx_ipv4.gateway = "21.1.1.1"

    # rx1_device config
    rx1_eth = rx1_device.ethernet
    rx1_eth.name = "rx1_eth"
    rx1_eth.mac = "00:00:00:00:00:bb"
    rx1_ipv4 = rx1_eth.ipv4
    rx1_ipv4.name = "rx1_ipv4"
    rx1_ipv4.address = "22.1.1.2"
    rx1_ipv4.prefix = 24
    rx1_ipv4.gateway = "22.1.1.1"
    rx1_bgpv4 = rx1_ipv4.bgpv4
    rx1_bgpv4.name = "rx1_bgpv4"
    rx1_bgpv4.as_type = "ebgp"
    rx1_bgpv4.dut_address = "22.1.1.1"
    rx1_bgpv4.as_number = 65200
    rx1_bgpv4.local_address = "22.1.1.2"
    rx1_rr = rx1_bgpv4.bgpv4_routes.bgpv4route(name="rx1_rr")[-1]
    rx1_rr.addresses.bgpv4routeaddress(
        count=1000, address="200.1.0.1", prefix=32
    )

    # rx2_device config
    rx2_eth = rx2_device.ethernet
    rx2_eth.name = "rx2_eth"
    rx2_eth.mac = "00:00:00:00:00:cc"
    rx2_ipv4 = rx2_eth.ipv4
    rx2_ipv4.name = "rx2_ipv4"
    rx2_ipv4.address = "23.1.1.2"
    rx2_ipv4.prefix = 24
    rx2_ipv4.gateway = "23.1.1.1"
    rx2_bgpv4 = rx2_ipv4.bgpv4
    rx2_bgpv4.name = "rx2_bgp"
    rx2_bgpv4.as_type = "ebgp"
    rx2_bgpv4.dut_address = "23.1.1.1"
    rx2_bgpv4.local_address = "23.1.1.2"
    rx2_bgpv4.as_number = 65200

    rx2_rr = rx2_bgpv4.bgpv4_routes.bgpv4route(name="rx2_rr")[-1]
    rx2_rr.addresses.bgpv4routeaddress(
        count=1000, address="200.1.0.1", prefix=32
    )

    # flow config
    flow = config.flows.flow(name="convergence_test")[-1]
    flow.tx_rx.device.tx_names = [tx_device.name]
    flow.tx_rx.device.rx_names = [rx1_rr.name, rx2_rr.name]

    flow.size.fixed = 1024
    flow.rate.percentage = 50
    flow.metrics.enable = True

    return conv_config


PRIMARY_ROUTES_NAME = "rx1_rr"
SECONDARY_ROUTES_NAME = "rx2_rr"
PRIMARY_PORT_NAME = "rx1"
# maximum convergence 3s
MAX_CON = 3000000


@pytest.mark.dut
def test_bgp_cp_dp_convergence(utils, cvg_api, bgp_convergence_config):
    """
    5. set advanced metric settings & start traffic
    6. Withdraw routes from primary path
    7. Wait for traffic to converge
    8. Obtain cp/dp convergence and validate against expected
    """

    # convergence config
    bgp_convergence_config.rx_rate_threshold = 90
    bgp_convergence_config.convergence_event = (
        bgp_convergence_config.ROUTE_ADVERTISE_WITHDRAW
    )

    cvg_api.set_config(bgp_convergence_config)

    # Start traffic
    cs = cvg_api.convergence_state()
    cs.transmit.state = cs.transmit.START
    cvg_api.set_state(cs)

    # Wait for traffic to reach configured line rate
    utils.wait_for(
        lambda: is_traffic_started(cvg_api),
        "traffic to start and reach configured line rate",
    )

    # Withdraw routes from primary path
    cs = cvg_api.convergence_state()
    cs.route.names = [PRIMARY_ROUTES_NAME]
    cs.route.state = cs.route.WITHDRAW
    cvg_api.set_state(cs)

    # Wait for traffic to converge
    utils.wait_for(
        lambda: is_traffic_converged(cvg_api), "traffic to converge"
    )

    # get convergence metrics
    request = cvg_api.convergence_request()
    request.convergence.flow_names = []
    convergence_metrics = cvg_api.get_results(request).flow_convergence

    for metrics in convergence_metrics:
        print(metrics.control_plane_data_plane_convergence_us)
        assert metrics.control_plane_data_plane_convergence_us < MAX_CON


def is_traffic_started(cvg_api):
    """
    Returns true if traffic in start state
    """
    flow_stats = get_flow_stats(cvg_api)
    return all(
        [
            int(fs.frames_rx_rate) == int(fs.frames_tx_rate) / 2
            for fs in flow_stats
        ]
    )


def is_traffic_converged(cvg_api):
    """
    Returns true if traffic in stop state
    """
    flow_stats = get_flow_stats(cvg_api)
    return all(
        [
            int(fs.frames_tx_rate) == int(fs.frames_rx_rate)
            for fs in flow_stats
            if fs.port_rx == "rx2"
        ]
    )


def get_flow_stats(cvg_api):
    request = cvg_api.convergence_request()
    request.metrics.flow_names = []
    return cvg_api.get_results(request).flow_metric
