import snappi


def test_basic_flow_stats(utils, settings):
    """
    Configure a raw TCP flow with,
    - tx port as source to rx port as destination
    - frame count 10000, each of size 128 bytes
    - transmit rate of 1000 packets per second
    Validate,
    - frames transmitted and received for configured flow is as expected
    """
    # host, port locations and ext is fetched from settings.json
    api = snappi.api(
        location=settings.location, ext=settings.ext, verify=False
    )

    config = api.config()
    tx, rx = config.ports.port(name="tx", location=settings.ports[0]).port(
        name="rx", location=settings.ports[1]
    )
    # this will allow us to take over ports that may already be in use
    config.options.port_options.location_preemption = True

    # configure layer 1 properties
    ly = config.layer1.layer1(name="ly")[-1]
    ly.port_names = [tx.name, rx.name]
    ly.speed = settings.speed
    ly.media = settings.media
    # configure capture
    cap = config.captures.capture(name="cap")[-1]
    cap.port_names = [rx.name]
    cap.format = cap.PCAPNG
    # configure flow properties
    flw = config.flows.flow(name="flw")[-1]
    # flow endpoints
    flw.tx_rx.port.tx_name = tx.name
    flw.tx_rx.port.rx_name = rx.name
    # allow fetching flow metrics
    flw.metrics.enable = True
    # configure rate, size, frame count
    flw.size.fixed = 128
    flw.rate.pps = 1000
    flw.duration.fixed_packets.packets = 1000
    # configure protocol headers with defaults fields
    flw.packet.ethernet().vlan().ipv4().tcp()
    # push configuration
    api.set_config(config)
    # start capture
    cs = api.capture_state()
    cs.state = cs.START
    api.set_capture_state(cs)
    # start transmitting configured flows
    ts = api.transmit_state()
    ts.state = ts.START
    api.set_transmit_state(ts)
    # create a query for flow metrics
    req = api.metrics_request()
    req.flow.flow_names = [flw.name]
    # wait for flow metrics to be as expected
    assert wait_for(lambda: metrics_ok(api, req)), "Metrics validation failed!"
    #while True:
    #    res = api.get_metrics(req)
    #    if all([1000 == m.frames_rx for m in res.flow_metrics]):
    #        break
    # get capture
    cr = api.capture_request()
    cr.port_name = rx.name
    pcap_bytes = api.get_capture(cr)
    # generate pcap in pwd
    with open("out.pcapng", "wb") as out:
        out.write(pcap_bytes.read())


def metrics_ok(api, req):
    res = api.get_metrics(req)
    if all([1000 == m.frames_rx for m in res.flow_metrics]):
        return True


def wait_for(func, timeout=15, interval=0.2):
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