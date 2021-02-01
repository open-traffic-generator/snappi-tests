from tests.convergence.bgp_convergence_config import *
import pytest


@pytest.mark.sonic
def test_bgp_dp_dp_convergence(api, bgp_convergence_config):
    """
    5. Get the frames tx rate
    6. Trigger withdraw routes by link down on port1
    7. Wait for sometime and stop the traffic
    8. Obtain tx frames and rx frames from stats and calculate
       dp/dp convergence
    """
    api.set_config(bgp_convergence_config)

    # Start traffic and get tx rate
    transmit_state = api.transmit_state()
    transmit_state.state = 'start'
    api.set_transmit_state(transmit_state)

    flow_stats = api.get_flow_metrics(api.flow_metrics_request())
    tx_frame_rate = flow_stats[0].frames_tx_rate

    # Trigger withdraw routes by link down on port1
    # TODO: Concrete implementation is still pending(#128)
    link_state = api.link_state(port_name=bgp_convergence_config.ports[0].name)
    link_state.state = "down"
    api.set_link_state(link_state)

    # Stop the traffic
    transmit_state = api.transmit_state()
    transmit_state.state = 'stop'
    api.set_transmit_state(transmit_state)

    # Get total tx frames & rx frames
    flow_stats = api.get_flow_metrics(api.flow_metrics_request())
    tx_frames = flow_stats[0].frames_tx
    rx_frames = flow_stats[0].frames_rx

    # Calculate Convergence
    dp_convergence = (tx_frames - rx_frames) / tx_frame_rate
    print("dp/dp convergence:", dp_convergence)
