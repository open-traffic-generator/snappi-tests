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
    api.set_config(bgp_convergence_config)

    # Start traffic
    ts = api.transmit_state()
    ts.state = ts.START
    api.set_transmit_state(ts)

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
    api.set_transmit_state(ts)

    # Wait for traffic to stop and get total tx frames & rx frames
    utils.wait_for(
        lambda: is_traffic_stopped(api), 'traffic to stop'
    )

    # get advanced data plane convergence metrics
    adv_analytics_request = api.advancedanalytics_request()
    adv_analytics_request.metric_names = adv_analytics_request.CONVERGENCE
    adv_analytics_request.flow_names = [
        bgp_convergence_config.flows[0].name
    ]

    # output the convergence metrics
    analytics = api.get_analytics(adv_analytics_request)

    # fail the test if cp/dp convergence takes longer than 500ms
    assert(
        all([m.convergence.control_plane_data_plane_convergence_ns < 500000000
            for m in analytics]))


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
    request = api.advancedmetrics_request()
    request.flow_names = []
    return api.get_flow_metrics(request)

