import snappi


def test_basic_flow_stats(settings):
    """
    Configure a raw TCP flow with,
    - tx port as source to rx port as destination
    - frame count 10000, each of size 128 bytes
    - transmit rate of 1000 packets per second
    Validate,
    - frames transmitted and received for configured flow is as expected
    """
    # host, port locations and ext is fetched from settings.json
    api = snappi.api(host=settings.api_server, ext=settings.ext)

    config = api.config()
    tx, rx = (
        config.ports
        .port(name='tx', location=settings.ports[0])
        .port(name='rx', location=settings.ports[1])
    )
    ly = config.layer1.layer1()[-1]
    ly.name = 'ly'
    ly.port_names = [tx.name, rx.name]
    ly.media = settings.media
    flw = config.flows.flow(name='flw')[-1]

    flw.size.fixed = 128
    flw.rate.pps = 1000
    flw.duration.fixed_packets.packets = 10000
    flw.tx_rx.port.tx_name = tx.name
    flw.tx_rx.port.rx_name = rx.name

    flw.packet.ethernet().vlan().ipv4().tcp()
    # this will allow us to take over ports that may already be in use
    config.options.port_options.location_preemption = True

    api.set_config(config)
    ts = api.transmit_state()
    ts.state = ts.START
    api.set_transmit_state(ts)

    while True:
        req = api.metrics_request()
        req.choice = req.FLOW
        metrics = api.get_metrics(req)
        if all([m.frames_tx == 10000 == m.frames_rx for m in metrics]):
            break
