

def test_tcp_unidir_flows(api, utils):
    """
    Configure a raw TCP flow with,
    - list of 6 src ports and 3 dst ports
    - 100 frames of 1518B size each
    - 10% line rate
    Validate,
    - tx/rx frame count and bytes are as expected
    """
    config = api.config()

    tx, rx = (
        config.ports
        .port(name='tx', location=utils.settings.ports[0])
        .port(name='rx', location=utils.settings.ports[1])
    )

    ly = config.layer1.layer1()[-1]
    ly.name = 'ly'
    ly.port_names = [tx.name, rx.name]
    ly.media = utils.settings.media
    ly.speed = utils.settings.speed

    flow = config.flows.flow(name='tx_flow')[-1]
    flow.tx_rx.port.tx_name = tx.name
    flow.tx_rx.port.rx_name = rx.name

    size = 128
    packets = 1000
    flow.size.fixed = size
    flow.duration.fixed_packets.packets = packets

    eth, ip, tcp = flow.packet.ethernet().ipv4().tcp()

    eth.src.value = '00:CD:DC:CD:DC:CD'
    eth.dst.value = '00:AB:BC:AB:BC:AB'

    ip.src.value = '1.1.1.2'
    ip.dst.value = '1.1.1.1'

    tcp.src_port.values = [5000, 5050, 5015, 5040, 5032, 5021]
    tcp.dst_port.values = [6000, 6015, 6050]

    # this will allow us to take over ports that may already be in use
    config.options.port_options.location_preemption = True

    utils.start_traffic(api, config, False)
    utils.wait_for(
        lambda: results_ok(api, utils, size, packets),
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
