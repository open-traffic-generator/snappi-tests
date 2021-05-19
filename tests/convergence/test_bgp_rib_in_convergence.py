import pytest

PRIMARY_ROUTES_NAME = 'rx1_rr'
SECONDARY_ROUTES_NAME = 'rx2_rr'
# maximum convergence 500ms
MAX_CONVERGENCE = 500000000


@pytest.mark.dut
def test_bgp_rib_in_convergence(api, utils, bgp_convergence_config):
    """
    5. set advanced metric settings & start traffic
    6. Trigger withdraw routes
    7. Wait for sometime and stop the traffic
    8. Obtain cp/dp convergence and validate against expected
    """
    # TODO: depending on rx ports (threshold = 90/n)
    # convergence config
    bgp_convergence_config.advanced.event.enable = True
    bgp_convergence_config.advanced.event.rx_rate_threshold.enable = True
    bgp_convergence_config.advanced.event.rx_rate_threshold.threshold = 45

    bgp_convergence_config.advanced.convergence.enable = True

    api.set_config(bgp_convergence_config)

    # withdraw primary routes and secondary routes
    route_state = api.route_state()
    route_state.state = route_state.WITHDRAW
    route_state.names = [PRIMARY_ROUTES_NAME, SECONDARY_ROUTES_NAME]
    api.set_route_state(route_state)

    # Start traffic
    ts = api.transmit_state()
    ts.state = ts.START
    api.set_transmit_state(ts)

    # Wait for traffic to start and get tx frame rate
    utils.wait_for(
        lambda: is_traffic_started(api), 'traffic to start'
    )

    # Advertise primary_routes and secondary routes
    route_state = api.route_state()
    route_state.state = route_state.ADVERTISE
    route_state.names = [PRIMARY_ROUTES_NAME, SECONDARY_ROUTES_NAME]
    api.set_route_state(route_state)

    # Wait for traffic to converge
    utils.wait_for(
        lambda: is_traffic_converged(api), 'traffic to converge'
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
    print([m.convergence.control_plane_data_plane_convergence_ns
           for m in analytics])
    assert(
        all([m.convergence.control_plane_data_plane_convergence_ns < 500000000
            for m in analytics]))


def is_traffic_started(api):
    """
    Returns true if traffic in start state
    """
    flow_stats = get_flow_stats(api)
    return all([int(fs.frames_tx_rate) > 0 for fs in flow_stats])


def is_traffic_converged(api):
    """
    Returns true if traffic in stop state
    """
    flow_stats = get_flow_stats(api)
    return all([int(fs.frames_rx_rate) == int(fs.frames_tx_rate) / 2
               for fs in flow_stats])


def get_flow_stats(api):
    request = api.advancedmetrics_request()
    request.flow_names = []
    return api.get_flow_metrics(request)

