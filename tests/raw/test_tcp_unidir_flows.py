import snappi
import pytest


@pytest.mark.parametrize(
    '   api_addr,           tx_addr,            rx_addr',
    [['127.0.0.1:11009', '127.0.0.1;1;1', '127.0.0.1;1;2']]
)
def test_tcp_bidir_flows(api_addr, tx_addr, rx_addr, utils):
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
    api = snappi.api(host=api_addr, ext=utils.get_ext())
    config = api.config()

    tx, rx = (
        config.ports
        .port(name='tx', location=tx_addr)
        .port(name='rx', location=rx_addr)
    )

    flow = config.flows.flow(name='tcp_flow')[-1]
    flow.tx_rx.port.tx_name = tx.name
    flow.tx_rx.port.rx_name = rx.name

    eth, ip, tcp = flow.packet.ethernet().ipv4().tcp()

    eth.src.value = '00:CD:DC:CD:DC:CD'
    eth.dst.value = '00:AB:BC:AB:BC:AB'

    ip.src.value = '1.1.1.2'
    ip.dst.value = '1.1.1.1'

    tcp.src_port.values = ['5000', '5050', '5015', '5040', '5032', '5021']
    tcp.dst_port.values = ['6000', '6015', '6050']

    flow.size.fixed = 128
    flow.duration.fixed_packets.packets = 1000

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
