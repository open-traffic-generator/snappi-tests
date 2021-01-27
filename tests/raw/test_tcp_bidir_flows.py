import json


def test_tcp_bidir_flows(api, utils):
    """
    Configure raw TCP bi-directional flows, each with,
    - list of 6 src ports and 3 dst ports
    - 100 frames of 1518B size each
    - 10% line rate
    Validate,
    - tx/rx frame count and bytes are as expected
    """
    config = api.config()
    # load JSON config from configs/
    with open(utils.get_test_config_path('tcp_bidir_flows.json')) as f:
        config_dict = json.load(f)
        config.deserialize(config_dict['config'])

    # update port locations
    config.ports[0].location = utils.settings.ports[0]
    config.ports[1].location = utils.settings.ports[1]
    # this will allow us to take over ports that may already be in use
    config.options.port_options.location_preemption = True

    # extract values to be used for assertion
    size = config.flows[0].size.fixed
    packets = config.flows[0].duration.fixed_packets.packets

    utils.start_traffic(api, config)

    utils.wait_for(
        lambda: results_ok(api, utils, size, packets * 2),
        'stats to be as expected', timeout_seconds=10
    )


def results_ok(api, utils, size, packets):
    """
    Returns true if stats are as expected, false otherwise.
    """
    port_results, flow_results = utils.get_all_stats(api)
    frames_ok = utils.total_frames_ok(port_results, flow_results, packets)
    bytes_ok = utils.total_bytes_ok(port_results, flow_results, packets * size)
    return frames_ok and bytes_ok
