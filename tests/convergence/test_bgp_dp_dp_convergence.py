from tests.convergence.bgp_convergence_config import bgp_convergence_config
import pytest


@pytest.mark.dut
def test_bgp_dp_dp_convergence(api, utils):
    """
    5. Get the frames tx rate
    6. Trigger withdraw routes by link down on port1
    7. Wait for sometime and stop the traffic
    8. Obtain tx frames and rx frames from stats and calculate
       dp/dp convergence
    """
    api.set_config(bgp_convergence_config)

    # Start traffic and get tx rate
    ts = api.transmit_state()
    ts.state = ts.START
    api.set_transmit_state(ts)

    utils.wait_for(
        lambda: is_traffic_started(api), 'traffic to start'
    )

    flow_stats = api.get_flow_metrics(api.flow_metrics_request())
    tx_frame_rate = flow_stats[0].frames_tx_rate

    # Trigger withdraw routes by link down on port1
    # TODO: Concrete implementation is still pending(#128)
    ls = api.link_state(port_name=bgp_convergence_config.ports[0].name)
    ls.state = ls.DOWN
    api.set_link_state(ls)

    # TODO: Add lambda function to check on port stats and when to stop traffic
    # Stop the traffic
    ts = api.transmit_state()
    ts.state = ts.STOP
    api.set_transmit_state(ts)

    # Get total tx frames & rx frames
    flow_stats = api.get_flow_metrics(api.flow_metrics_request())
    tx_frames = flow_stats[0].frames_tx
    rx_frames = flow_stats[0].frames_rx

    # Calculate Convergence
    dp_convergence = (tx_frames - rx_frames) / tx_frame_rate
    print("dp/dp convergence:", dp_convergence)


def is_traffic_started(api):
    """
    Returns true if traffic in start state
    """
    flow_stats = api.get_flow_metrics(api.flow_metrics_request())
    tx_frame_rate = flow_stats[0].frames_tx_rate

    if int(tx_frame_rate) > 0:
        return True
    else:
        return False
