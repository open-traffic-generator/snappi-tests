def test_tcp_bidir_flows(api, tx_addr, rx_addr, utils):
    """
    Configure a raw TCP flow with,
    - list of 6 src ports and 3 dst ports
    - 100 frames of 1518B size each
    - 10% line rate
    Validate,
    - tx/rx frame count and bytes are as expected
    - all captured frames have expected src and dst ports
    """
    size = 128
    packets = 1000
    config = api.config()

    tx, rx = (
        config.ports
        .port(name='tx', location=tx_addr)
        .port(name='rx', location=rx_addr)
    )

    # flow1
    flow1 = config.flows.flow(name='tcp_flow1')[0]
    flow1.tx_rx.port.tx_name = tx.name
    flow1.tx_rx.port.rx_name = rx.name

    eth, ip, tcp = flow1.packet.ethernet().ipv4().tcp()

    eth.src.value = '00:CD:DC:CD:DC:CD'
    eth.dst.value = '00:AB:BC:AB:BC:AB'

    ip.src.value = '1.1.1.2'
    ip.dst.value = '1.1.1.1'

    tcp.src_port.values = ['5000', '5050', '5015', '5040', '5032', '5021']
    tcp.dst_port.values = ['6000', '6015', '6050']

    flow1.size.fixed = 128
    flow1.duration.fixed_packets.packets = 1000

    # flow2
    flow2 = config.flows.flow(name='tcp_flow2')[1]
    flow2.tx_rx.port.tx_name = rx.name
    flow2.tx_rx.port.rx_name = tx.name

    eth, ip, tcp = flow2.packet.ethernet().ipv4().tcp()

    eth.src.value = '00:AB:BC:AB:BC:AB'
    eth.dst.value = '00:CD:DC:CD:DC:CD'

    ip.src.value = '1.1.1.1'
    ip.dst.value = '1.1.1.2'

    tcp.src_port.values = ['5000', '5050', '5015', '5040', '5032', '5021']
    tcp.dst_port.values = ['6000', '6015', '6050']

    flow2.size.fixed = 128
    flow2.duration.fixed_packets.packets = 1000

    utils.start_traffic(api, config)
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
