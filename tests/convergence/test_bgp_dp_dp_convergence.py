from tests.convergence.bgp_convergence_config import bgp_convergence_config
import pytest


@pytest.mark.dut
def test_bgp_dp_dp_convergence(api, utils, bgp_convergence_config):
    """
    5. Get the frames tx rate
    6. Trigger withdraw routes by link down on port1
    7. Wait for sometime and stop the traffic
    8. Obtain tx frames and rx frames from stats and calculate
       dp/dp convergence
    """

    api.set_config(bgp_convergence_config)
    # name of the port that should be shutdown to trigger withdraw route
    primary_rx_port = bgp_convergence_config.ports[1].name

    # Start traffic
    ts = api.transmit_state()
    ts.state = ts.START
    api.set_transmit_state(ts)

    # Wait for traffic to start and get tx frame rate
    utils.wait_for(
        lambda: is_traffic_started(api), 'traffic to start'
    )
    req = api.metrics_request()
    req.choice = req.FLOW
    flow_stats = api.get_metrics(req)
    tx_frame_rate = flow_stats[0].frames_tx_rate

    # Trigger withdraw routes by doing a link down on port1
    ls = api.link_state()
    ls.port_names = [primary_rx_port]
    ls.state = ls.DOWN
    api.set_link_state(ls)

    # Wait for port to go down
    utils.wait_for(
        lambda: is_port_rx_stopped(api, primary_rx_port), 'port rx to stop'
    )

    # Stop traffic
    ts = api.transmit_state()
    ts.state = ts.STOP
    api.set_transmit_state(ts)

    # Wait for traffic to stop and get total tx frames & rx frames
    utils.wait_for(
        lambda: is_traffic_stopped(api), 'traffic to stop'
    )
    req = api.metrics_request()
    req.choice = req.FLOW
    flow_stats = api.get_metrics(req)
    tx_frames = flow_stats[0].frames_tx
    rx_frames = sum([fs.frames_rx for fs in flow_stats])

    # Calculate Convergence
    dp_convergence = (tx_frames - rx_frames) * 1000 / tx_frame_rate
    print("dp/dp convergence: {} ms".format(int(dp_convergence)))


def is_traffic_started(api):
    """
    Returns true if traffic in start state
    """
    req = api.metrics_request()
    req.choice = req.FLOW
    flow_stats = api.get_metrics(req)
    return all([int(fs.frames_tx_rate) > 0 for fs in flow_stats])


def is_traffic_stopped(api):
    """
    Returns true if traffic in stop state
    """
    req = api.metrics_request()
    req.choice = req.FLOW
    flow_stats = api.get_metrics(req)
    return all([int(fs.frames_tx_rate) == 0 for fs in flow_stats])


def is_port_rx_stopped(api, port_name):
    """
    Returns true if port is down
    """
    req = api.metrics_request()
    req.port.port_names = [port_name]
    port_stats = api.get_metrics(req)
    if int(port_stats[0].frames_rx_rate) == 0:
        return True
    return False

