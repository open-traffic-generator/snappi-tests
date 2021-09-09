import pytest


@pytest.mark.skip(
    reason="https://github.com/open-traffic-generator/snappi-ixnetwork/issues/443"
)
@pytest.mark.device
def test_ip_v4v6_device_and_raw_capture(api, utils):
    """
    Configure ipv4 and ipv6 dual stack devices, then configure flows for
    devices and create raw ipv4 and ipv6 flows which will be.
    validation:
    verify the flows transmission from tx to rx with no loss.
    verify mac and ipv4/ipv6 on each packet captured.
    """
    config = api.config()

    size = 128
    packets = 1000
    src_mac = "00:10:10:20:20:10"
    dst_mac = "00:10:10:20:20:20"
    mac_step = "00:00:00:00:00:01"

    src_ipv4 = "10.1.1.1"
    dst_ipv4 = "10.1.1.2"
    ipv4_step = "0.0.1.0"

    src_ipv6 = "abcd::1a"
    dst_ipv6 = "abcd::2a"
    ipv6_step = "1::"

    count = 1

    # Ports configuration
    tx, rx = config.ports.port(
        name="tx", location=utils.settings.ports[0]
    ).port(name="rx", location=utils.settings.ports[1])
    l1 = config.layer1.layer1()[-1]
    l1.name = "L1 Settings"
    l1.port_names = [tx.name, rx.name]
    l1.speed = utils.settings.speed
    l1.media = utils.settings.media
    l1.promiscuous = utils.settings.promiscuous

    cap = config.captures.capture(name="c1")[-1]
    cap.port_names = [rx.name]
    cap.format = cap.PCAP

    # Device configuration
    tx_dev, rx_dev = config.devices.device().device()
    tx_dev.name = "tx_dev"
    rx_dev.name = "rx_dev"
    tx_dev.container_name = tx.name
    rx_dev.container_name = rx.name
    tx_eth = tx_dev.ethernet
    rx_eth = rx_dev.ethernet
    # Ethernet configuration
    tx_eth.name = "tx_eth"
    tx_eth.mac = src_mac
    # Ipv4 configuration
    tx_ipv4 = tx_eth.ipv4
    tx_ipv4.name = "tx_ipv4"
    tx_ipv4.address = src_ipv4
    tx_ipv4.gateway = dst_ipv4
    tx_ipv4.prefix = 24
    # Ipv6 configuration
    tx_ipv6 = tx_eth.ipv6
    tx_ipv6.name = "tx_ipv6"
    tx_ipv6.address = src_ipv6
    tx_ipv6.gateway = dst_ipv6
    tx_ipv6.prefix = 48
    # Ethernet configuration
    rx_eth.name = "rx_eth"
    rx_eth.mac = dst_mac
    # Ipv4 configuration
    rx_ipv4 = rx_eth.ipv4
    rx_ipv4.name = "rx_ipv4"
    rx_ipv4.address = dst_ipv4
    rx_ipv4.gateway = src_ipv4
    rx_ipv4.prefix = 24
    # Ipv6 configuration
    rx_ipv6 = rx_eth.ipv6
    rx_ipv6.name = "rx_ipv6"
    rx_ipv6.address = dst_ipv6
    rx_ipv6.gateway = src_ipv6
    rx_ipv6.prefix = 48

    # TODO Add protocol summary once it is supported

    # Flows configuration
    f1, f2, f3, f4 = (
        config.flows.flow(name="FlowIpv4Device")
        .flow(name="FlowIpv6Device")
        .flow(name="FlowIpv4Raw")
        .flow(name="FlowIpv6Raw")
    )
    f1.tx_rx.device.tx_names = [tx_ipv4.name]
    f1.tx_rx.device.rx_names = [rx_ipv4.name]
    f1.size.fixed = size
    f1.duration.fixed_packets.packets = packets
    f1.rate.percentage = 10

    f2.tx_rx.device.tx_names = [tx_ipv6.name]
    f2.tx_rx.device.rx_names = [rx_ipv6.name]
    f2.size.fixed = size
    f2.duration.fixed_packets.packets = packets
    f2.rate.percentage = 10

    f3.tx_rx.port.tx_name = tx.name
    f3.tx_rx.port.rx_name = rx.name
    f3.packet.ethernet().ipv4()
    eth = f3.packet[0]
    ipv4 = f3.packet[1]
    # Ethernet header configuration
    eth.src.increment.start = src_mac
    eth.src.increment.step = mac_step
    eth.src.increment.count = count
    eth.dst.decrement.start = dst_mac
    eth.dst.decrement.step = mac_step
    eth.dst.decrement.count = count
    # Ipv4 header configuration
    ipv4.src.increment.start = src_ipv4
    ipv4.src.increment.step = ipv4_step
    ipv4.src.increment.count = count
    ipv4.dst.increment.start = dst_ipv4
    ipv4.dst.increment.step = ipv4_step
    ipv4.dst.increment.count = count

    f3.size.fixed = size
    f3.duration.fixed_packets.packets = packets

    f4.tx_rx.port.tx_name = tx.name
    f4.tx_rx.port.rx_name = rx.name
    f4.packet.ethernet().ipv6()
    eth = f4.packet[0]
    ipv6 = f4.packet[1]
    # Ethernet header configuration
    eth.src.increment.start = src_mac
    eth.src.increment.step = mac_step
    eth.src.increment.count = count
    eth.dst.decrement.start = dst_mac
    eth.dst.decrement.step = mac_step
    eth.dst.decrement.count = count
    # Ipv6 header configuration
    ipv6.src.increment.start = src_ipv6
    ipv6.src.increment.step = ipv6_step
    ipv6.src.increment.count = count
    ipv6.dst.increment.start = dst_ipv6
    ipv6.dst.increment.step = ipv6_step
    ipv6.dst.increment.count = count
    f4.size.fixed = size
    f4.duration.fixed_packets.packets = packets

    f1.metrics.enable = True

    f2.metrics.enable = True

    f3.metrics.enable = True

    f4.metrics.enable = True

    # Starting transmit on flows
    utils.start_traffic(api, config)

    print("Analyzing flow and port metrics ...")
    utils.wait_for(
        lambda: results_ok(api, utils, size, packets * 4),
        "stats to be as expected",
        timeout_seconds=10,
    )

    print("Stopping transmit ...")
    utils.stop_traffic(api, config)

    print("Capture validation ...")
    captures_ok(api, config, utils, size, packets * 4)


def results_ok(api, utils, size, packets):
    """
    Returns true if stats are as expected, false otherwise.
    """
    port_results, flow_results = utils.get_all_stats(api)
    frames_ok = utils.total_frames_ok(port_results, flow_results, packets)
    bytes_ok = utils.total_bytes_ok(port_results, flow_results, packets * size)
    return frames_ok and bytes_ok


def captures_ok(api, cfg, utils, size, packets):
    """
    Returns normally if patterns in captured packets are as expected.
    """
    src_mac = [[0x00, 0x10, 0x10, 0x20, 0x20, 0x10 + i] for i in range(10)]
    dst_mac = [[0x00, 0x10, 0x10, 0x20, 0x20, 0x20 - i] for i in range(10)]
    src_ip = [[0x0A, 0x01, 0x01 + i, 0x01] for i in range(10)]
    dst_ip = [[0x0A, 0x01, 0x01 + i, 0x02] for i in range(10)]
    src_ip6 = [
        [
            0xAB,
            0xCD + i,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x1A,
        ]
        for i in range(10)
    ]
    dst_ip6 = [
        [
            0xAB,
            0xCD + i,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x2A,
        ]
        for i in range(10)
    ]

    cap_dict = utils.get_all_captures(api, cfg)
    assert len(cap_dict) == 1
    size_dt = {size: [0 for i in range(10)]}

    for index, b in enumerate(cap_dict[list(cap_dict.keys())[0]]):
        try:
            i = dst_mac.index(b[0:6])
        except Exception:
            # To avoid packets that are not generated by configured flows
            continue
        assert b[0:6] == dst_mac[i] and b[6:12] == src_mac[i]
        if b[14] == 0x45:
            assert b[26:30] == src_ip[i] and b[30:34] == dst_ip[i]
        else:
            assert b[22:38] == src_ip6[i] and b[38:54] == dst_ip6[i]
        assert len(b) == size
        size_dt[len(b)][i] += 1

    assert sum(size_dt[size]) == packets
