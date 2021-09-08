def test_raw_tcp_flow_capture(api, utils):
    """
    Configures the 2 raw flows ipv4 and ipv6 with dual stack and tcp,
    on top of it. traffic shall flow from tx port to rx ports with specific
    size and packets.
    Validation:
    The port and flow metrics shall have no loss and capture the packets
    and verify the mac, ip and tcp port on each packet.
    """
    config = api.config()

    size = 256
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

    src_tcp = 5000
    dst_tcp = 2000
    tcp_step = 1

    count = 10

    # Ports configuration
    tx, rx = config.ports.port(
        name="tx", location=utils.settings.ports[0]
    ).port(name="rx", location=utils.settings.ports[1])
    l1 = config.layer1.layer1()[-1]
    l1.name = "L1 Settings"
    l1.port_names = [tx.name, rx.name]
    l1.speed = utils.settings.speed
    l1.media = utils.settings.media

    cap = config.captures.capture(name="c1")[-1]
    cap.port_names = [rx.name]
    cap.format = cap.PCAP

    # Flows configuration
    f1, f2 = config.flows.flow(name="FlowIpv4Raw").flow(name="FlowIpv6Raw")

    f1.tx_rx.port.tx_name = tx.name
    f1.tx_rx.port.rx_name = rx.name
    f1.packet.ethernet().ipv4().tcp()
    eth = f1.packet[0]
    ipv4 = f1.packet[1]
    tcp = f1.packet[-1]
    # Ethernet header Config
    eth.src.increment.start = src_mac
    eth.src.increment.step = mac_step
    eth.src.increment.count = count
    eth.dst.decrement.start = dst_mac
    eth.dst.decrement.step = mac_step
    eth.dst.decrement.count = count
    # Ipv4 header Config
    ipv4.src.increment.start = src_ipv4
    ipv4.src.increment.step = ipv4_step
    ipv4.src.increment.count = count
    ipv4.dst.increment.start = dst_ipv4
    ipv4.dst.increment.step = ipv4_step
    ipv4.dst.increment.count = count
    # Tcp header Config
    tcp.src_port.increment.start = src_tcp
    tcp.src_port.increment.step = tcp_step
    tcp.src_port.increment.count = count
    tcp.dst_port.increment.start = dst_tcp
    tcp.dst_port.increment.step = tcp_step
    tcp.dst_port.increment.count = count

    f1.size.fixed = size
    f1.duration.fixed_packets.packets = packets

    f2.tx_rx.port.tx_name = tx.name
    f2.tx_rx.port.rx_name = rx.name
    f2.packet.ethernet().ipv6().tcp()
    eth = f2.packet[0]
    ipv6 = f2.packet[1]
    tcp = f2.packet[-1]
    # Ethernet header Config
    eth.src.increment.start = src_mac
    eth.src.increment.step = mac_step
    eth.src.increment.count = count
    eth.dst.decrement.start = dst_mac
    eth.dst.decrement.step = mac_step
    eth.dst.decrement.count = count
    # Ipv6 header Config
    ipv6.src.increment.start = src_ipv6
    ipv6.src.increment.step = ipv6_step
    ipv6.src.increment.count = count
    ipv6.dst.increment.start = dst_ipv6
    ipv6.dst.increment.step = ipv6_step
    ipv6.dst.increment.count = count
    # Tcp header Config
    tcp.src_port.increment.start = src_tcp
    tcp.src_port.increment.step = tcp_step
    tcp.src_port.increment.count = count
    tcp.dst_port.increment.start = dst_tcp
    tcp.dst_port.increment.step = tcp_step
    tcp.dst_port.increment.count = count

    f2.size.fixed = size
    f2.duration.fixed_packets.packets = packets

    f1.metrics.enable = True

    f2.metrics.enable = True

    # Starting transmit on flows
    utils.start_traffic(api, config)

    print("Analyzing flow and port metrics ...")
    utils.wait_for(
        lambda: results_ok(api, utils, size, packets * 2),
        "stats to be as expected",
        timeout_seconds=10,
    )

    print("Stopping transmit ...")
    utils.stop_traffic(api)

    print("Capture validation ...")
    captures_ok(api, config, utils, size, packets * 2)


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
    src_port = [[0x13, 0x88 + i] for i in range(10)]
    dst_port = [[0x07, 0xD0 + i] for i in range(10)]

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
            assert b[34:36] == src_port[i] and b[36:38] == dst_port[i]
        else:
            assert b[22:38] == src_ip6[i] and b[38:54] == dst_ip6[i]
            assert b[54:56] == src_port[i] and b[56:58] == dst_port[i]
        assert len(b) == size
        size_dt[len(b)][i] += 1

    assert sum(size_dt[size]) == packets
