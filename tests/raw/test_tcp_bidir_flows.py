import snappi
import pytest


@pytest.mark.parametrize(
    '   api_addr,           tx_addr,            rx_addr', 
    [['127.0.0.1:11009', '127.0.0.1;1;1', '127.0.0.1;1;2']]
)
def test_tcp_bidir_flows(api_addr, tx_addr, rx_addr):
    """
    Configure a raw TCP flow with,
    - list of 6 src ports and 3 dst ports
    - 100 frames of 1518B size each
    - 10% line rate
    Validate,
    - tx/rx frame count and bytes are as expected
    - all captured frames have expected src and dst ports
    """
    api = snappi.Api()
    config = api.config()

    tx, rx = (
        config.ports
        .port(name='tx', location=tx_addr)
        .port(name='rx', location=rx_addr)
    )

    flow = config.flows.flow(name='tcp_flow')
    flow.packet()
