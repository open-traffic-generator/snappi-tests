import snappi


def hello_snappi():
    """
    This script does following:
    - Send 1000 packets back and forth between the two ports at a rate of
      1000 packets per second.
    - Validate that total packets sent and received on both interfaces is as
      expected using **port metrics**.
    - Validate that captured UDP packets on both the ports have expected
      destination UDP port.
    """
    # create a new API instance where host points to controller
    api = snappi.api(host='https://localhost')
    # and a traffic configuration to be pushed later on
    cfg = api.config()

    # add two ports where location points to address of athena traffic-engine
    p1, p2 = (
        cfg.ports
        .port(name='p1', location='localhost:5555')
        .port(name='p2', location='localhost:5556')
    )

    # add layer 1 property to configure same speed on both ports
    ly = cfg.layer1.layer1(name='ly')[-1]
    ly.port_names = [p1.name, p2.name]
    ly.speed = ly.SPEED_1_GBPS

    # enable packet capture on both ports
    cp = cfg.captures.capture(name='cp')[-1]
    cp.port_names = [p1.name, p2.name]

    # add two traffic flows
    f1, f2 = cfg.flows.flow(name='flow p1->p2').flow(name='flow p2->p1')
    # and assign source and destination ports for each
    f1.tx_rx.port.tx_name, f1.tx_rx.port.rx_name = p1.name, p2.name
    f2.tx_rx.port.tx_name, f2.tx_rx.port.rx_name = p2.name, p1.name

    # configure packet size, rate and duration for both flows
    f1.size.fixed, f2.size.fixed = 128, 256
    for f in cfg.flows:
        f.duration.fixed_packets.packets = 1000
        f.rate.pps = 1000

    # configure packet with Ethernet, IPv4 and UDP headers for both flows
    eth1, ip1, udp1 = f1.packet.ethernet().ipv4().udp()
    eth2, ip2, udp2 = f2.packet.ethernet().ipv4().udp()

    # set source and destination MAC addresses
    eth1.src.value, eth2.dst.value = ('00:AA:00:00:04:00', ) * 2
    eth2.src.value, eth1.dst.value = ('00:AA:00:00:00:AA', ) * 2

    # set source and destination IPv4 addresses
    ip1.src.value, ip2.dst.value = ('10.0.0.1', ) * 2
    ip2.src.value, ip1.dst.value = ('10.0.0.2', ) * 2

    # set incrementing port numbers as source UDP ports
    udp1.src_port.increment.start = 5000
    udp1.src_port.increment.step = 2
    udp1.src_port.increment.count = 10

    udp2.src_port.increment.start = 6000
    udp2.src_port.increment.step = 4
    udp2.src_port.increment.count = 10

    # assign list of port numbers as destination UDP ports
    udp1.dst_port.values = [7001, 7010, 7015, 7018]
    udp2.dst_port.values = [8001, 8010, 8015, 8018]

    # push configuration
    api.set_config(cfg)

    # start packet capture on all configured ports
    cs = api.capture_state()
    cs.state = cs.START
    api.set_capture_state(cs)

    # start transmitting configured flows
    ts = api.transmit_state()
    ts.state = ts.START
    api.set_transmit_state(ts)

    assert metrics_ok(api, cfg)
    assert captures_ok(api, cfg)


def metrics_ok(api, cfg):
    # create a port metrics request and filter based on port names
    req = api.metrics_request()
    req.port.port_names = [p.name for p in cfg.ports]
    # include only sent and received packet counts
    req.port.column_names = [req.port.FRAMES_TX, req.port.FRAMES_RX]

    import time
    start = time.time()
    exp_pkt = sum([f.duration.fixed_packets.packets for f in cfg.flows])

    while time.time() - start < 30:
        # fetch port metrics
        res = api.get_metrics(req)
        # calculate total frames sent and received across all configured ports
        total_tx = sum([m.frames_tx for m in res.port_metrics])
        total_rx = sum([m.frames_rx for m in res.port_metrics])

        if exp_pkt == total_tx == total_rx:
            return True

        print(total_tx, total_rx)
        time.sleep(0.5)

    return False


def captures_ok(api, cfg):
    import dpkt

    for p in cfg.ports:
        # figure out expected destination UDP ports on current port
        i = 0 if p.name == cfg.flows[0].tx_rx.port.rx_name else 1
        dst_ports = cfg.flows[i].packet[-1].dst_port.values

        # create capture request and filter based on port name
        req = api.capture_request()
        req.port_name = p.name
        # fetch captured pcap bytes and feed it to pcap parser dpkt
        pcap = dpkt.pcap.Reader(api.get_capture(req))
        for _, buf in pcap:
            # check if the destination UDP port is among what was configured
            eth = dpkt.ethernet.Ethernet(buf)
            if eth.data.data.dport not in dst_ports:
                return False

    return True


if __name__ == '__main__':
    hello_snappi()
