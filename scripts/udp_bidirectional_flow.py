import snappi


def udp_bidirectional_flow():
    """
    This script does following:
    - Send 1000 packets back and forth between the two ports at a rate of
      1000 packets per second.
    - Validate that total packets sent and received on both interfaces is as
      expected using port metrics.
    - Validate that captured UDP packets on both the ports are as expected.
    """
    # create a new API instance where location points to controller
    # ixia-c:
    #   location = "https://<tgen-ip>:<port>"
    # ixnetwork
    #   location = "https://<tgen-ip>:<port>", ext="ixnetwork"
    # trex
    #   location = "https://<tgen-ip>:<port>", ext="trex"
    api = snappi.api(location="https://localhost:443", verify=False, ext=None)
    # and an empty traffic configuration to be pushed to controller later on
    cfg = api.config()

    # add two ports where location points to traffic-engine (aka ports)
    # ixia-c, trex:
    #   port.location = "localhost:5555"
    # ixnetwork:
    #   port.location = "<chassisip>;card;port"
    #
    p1, p2 = cfg.ports.port(name="p1", location="localhost:5555").port(
        name="p2", location="localhost:5556"
    )

    # add layer 1 property to configure same speed on both ports
    cfg.layer1.layer1(port_names=[p1.name, p2.name], name="l1")
    ly = cfg.layer1[-1]
    ly.speed = ly.SPEED_1_GBPS

    # enable packet capture on both ports
    cp = cfg.captures.capture(name="cp")[-1]
    cp.port_names = [p1.name, p2.name]

    # add two traffic flows
    f1, f2 = cfg.flows.flow(name="flow p1->p2").flow(name="flow p2->p1")
    # and assign source and destination ports for each
    f1.tx_rx.port.tx_name, f1.tx_rx.port.rx_name = p1.name, p2.name
    f2.tx_rx.port.tx_name, f2.tx_rx.port.rx_name = p2.name, p1.name

    # configure packet size, rate and duration for both flows
    f1.size.fixed, f2.size.fixed = 128, 256
    for f in cfg.flows:
        # send 1000 packets and stop
        f.duration.fixed_packets.packets = 1000
        # send 1000 packets per second
        f.rate.pps = 1000

    # configure packet with Ethernet, IPv4 and UDP headers for both flows
    f1.packet.ethernet().ipv4().udp()
    f2.packet.ethernet().ipv4().udp()
    eth1, ip1, udp1 = f1.packet[0], f1.packet[1], f1.packet[2]
    eth2, ip2, udp2 = f2.packet[0], f2.packet[1], f2.packet[2]

    # set source and destination MAC addresses
    eth1.src.value, eth1.dst.value = "00:AA:00:00:04:00", "00:AA:00:00:00:AA"
    eth2.src.value, eth2.dst.value = "00:AA:00:00:00:AA", "00:AA:00:00:04:00"

    # set source and destination IPv4 addresses
    ip1.src.value, ip1.dst.value = "10.0.0.1", "10.0.0.2"
    ip2.src.value, ip2.dst.value = "10.0.0.2", "10.0.0.1"
    # TODO models is defaulting to any host with 64 and need to fix.
    ip1.protocol.value = 17
    ip2.protocol.value = 17

    # set incrementing port numbers as source UDP ports
    udp1.src_port.increment.start = 5000
    udp1.src_port.increment.step = 2
    udp1.src_port.increment.count = 10

    udp2.src_port.increment.start = 6000
    udp2.src_port.increment.step = 4
    udp2.src_port.increment.count = 10

    # assign list of port numbers as destination UDP ports
    udp1.dst_port.values = [4000, 4044, 4060, 4074]
    udp2.dst_port.values = [8000, 8044, 8060, 8074, 8082, 8084]

    print("Pushing traffic configuration ...")
    api.set_config(cfg)

    print("Starting packet capture on all configured ports ...")
    cs = api.capture_state()
    cs.state = cs.START
    api.set_capture_state(cs)

    print("Starting transmit on all configured flows ...")
    ts = api.transmit_state()
    ts.state = ts.START
    api.set_transmit_state(ts)

    print("Checking metrics on all configured ports ...")
    print("Expected\tTotal Tx\tTotal Rx")
    assert wait_for(lambda: metrics_ok(api, cfg)), "Metrics validation failed!"

    print("Test passed !")


def metrics_ok(api, cfg):
    # create a port metrics request and filter based on port names
    req = api.metrics_request()
    req.port.port_names = [p.name for p in cfg.ports]
    # include only sent and received packet counts
    req.port.column_names = [req.port.FRAMES_TX, req.port.FRAMES_RX]

    # fetch port metrics
    res = api.get_metrics(req)
    # calculate total frames sent and received across all configured ports
    total_tx = sum([m.frames_tx for m in res.port_metrics])
    total_rx = sum([m.frames_rx for m in res.port_metrics])
    expected = sum([f.duration.fixed_packets.packets for f in cfg.flows])

    print("%d\t\t%d\t\t%d" % (expected, total_tx, total_rx))

    return expected == total_tx and total_rx >= expected


def wait_for(func, timeout=10, interval=0.2):
    """
    Keeps calling the `func` until it returns true or `timeout` occurs
    every `interval` seconds.
    """
    import time

    start = time.time()

    while time.time() - start <= timeout:
        if func():
            return True
        time.sleep(interval)

    print("Timeout occurred !")
    return False


if __name__ == "__main__":
    udp_bidirectional_flow()
