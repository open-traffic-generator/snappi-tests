import pytest

PRIMARY_ROUTES_NAME = 'rx1_rr'
SECONDARY_ROUTES_NAME = 'rx2_rr'
# maximum convergence 500ms
MAX_CONVERGENCE = 500000000


@pytest.mark.dut
def test_bgp_cp_dp_convergence(api, utils, bgp_convergence_config):
    """
    5. set advanced metric settings & start traffic
    6. Trigger withdraw routes
    7. Wait for sometime and stop the traffic
    8. Obtain cp/dp convergence and validate against expected
    """
    api.set_config(api.config())
    response = api.set_config(bgp_convergence_config)
    assert(len(response.errors)) == 0

    # build the configuration for advanced convergence metrics
    adv_metrics = api.advancedmetrics_config()
    adv_metrics.convergence.enable = True
    adv_metrics.convergence.rx_rate_threshold = 90
    api.set_advanced_metrics(adv_metrics)

    # Start traffic
    ts = api.transmit_state()
    ts.state = ts.START
    response = api.set_transmit_state(ts)
    assert(len(response.errors)) == 0

    # Wait for traffic to start and get tx frame rate
    utils.wait_for(
        lambda: is_traffic_started(api), 'traffic to start'
    )

    # withdraw primary routes using the primary_routes_name
    route_state = api.route_state()
    route_state.state = route_state.WITHDRAW
    route_state.names = [PRIMARY_ROUTES_NAME]
    api.set_route_state(route_state)

    # TODO: Add wait_for to check withdraw has triggered

    # Stop traffic(optional)
    ts = api.transmit_state()
    ts.state = ts.STOP
    response = api.set_transmit_state(ts)
    assert(len(response.errors)) == 0

    # Wait for traffic to stop and get total tx frames & rx frames
    utils.wait_for(
        lambda: is_traffic_stopped(api), 'traffic to stop'
    )

    # get advanced data plane convergence metrics
    adv_metrics_request = api.advancedmetrics_request()
    adv_metrics_request.convergence.flow_names = [
        bgp_convergence_config.flows[0].name
    ]
    adv_metrics_request.convergence.event_sources = [
        PRIMARY_ROUTES_NAME
    ]

    # output the convergence metrics
    adv_metrics = api.get_advanced_metrics(adv_metrics_request)

    # fail the test if cp/dp convergence takes longer than 500ms
    assert(all([m.control_plane_data_plane_convergence_ns < 500000000
                for m in adv_metrics.convergence_metrics]))


def is_traffic_started(api):
    """
    Returns true if traffic in start state
    """
    flow_stats = get_flow_stats(api)
    return all([int(fs.frames_tx_rate) > 0 for fs in flow_stats])


def is_traffic_stopped(api):
    """
    Returns true if traffic in stop state
    """
    flow_stats = get_flow_stats(api)
    return all([int(fs.frames_tx_rate) == 0 for fs in flow_stats])


def get_flow_stats(api):
    request = api.metrics_request()
    request.flow.flow_names = []
    return api.get_metrics(request).flow_metrics

