import pytest


@pytest.mark.e2e
@pytest.mark.parametrize('lossless_priorities', [[3, 4]])
def test_pfc_pause_e2e(api, settings, utils, lossless_priorities):
    """
    Configure ports where,
    - tx port can only respond to pause frames for `lossless_priorities`
    - rx port is capable of sending pause frames for all priorities
    Configure 8 raw IPv4 flows on tx port where,
    - each flow is mapped to corresponding PHB_CS and priority queue value
    - each flow sends 100K frames at 10% line rate and with start delay of 1s
    Configure one raw PFC Pause flow on rx port where,
    - pause frames are sent for 20 seconds (pause storm)
    Validate,
    - tx/rx frame count is 600K before and 800K after pause storm
    - rx frame count for flows pertaining to `lossless_priorities` is 0 before
      and 100K after pause storm
    - rx frame count for rest of the flows is 100K before and after pause storm
    """

    size = 128
    packets = 100000
    config = api.config()
    tx = config.ports.port(name="raw_tx", location=settings.ports[0])[-1]
    rx = config.ports.port(name="raw_rx", location=settings.ports[1])[-1]
    config.options.port_options.location_preemption = True

    tx_l1, rx_l1 = config.layer1.layer1(port_names=tx).layer1(port_names=rx)
    tx_l1.speed = settings.speed
    tx_l1.media = settings.media
    qbb = tx_l1.flow_control.ieee_802_1qbb
    qbb.pfc_class_0 = 0 if 0 in lossless_priorities else None
    qbb.pfc_class_1 = 1 if 1 in lossless_priorities else None
    qbb.pfc_class_2 = 2 if 2 in lossless_priorities else None
    qbb.pfc_class_3 = 3 if 3 in lossless_priorities else None
    qbb.pfc_class_4 = 4 if 4 in lossless_priorities else None
    qbb.pfc_class_5 = 5 if 5 in lossless_priorities else None
    qbb.pfc_class_6 = 6 if 6 in lossless_priorities else None
    qbb.pfc_class_7 = 7 if 7 in lossless_priorities else None

    rx_l1.speed = settings.speed
    rx_l1.media = settings.media
    qbb = rx_l1.flow_control.ieee_802_1qbb

    for i in range(8):
        flow = config.flows.flow(name="tx_p%d" % i)[-1]
        flow.tx_rx.port.tx_name = tx.name
        flow.tx_rx.port.rx_name = rx.name
        flow.packet.ethernet().ipv4()
        eth = flow.packet[0]
        ipv4 = flow.packet[1]
        eth.src.value = '00:CD:DC:CD:DC:CD'
        eth.dst.value = '00:AB:BC:AB:BC:AB'
        eth.pfc_queue.value = i
        ipv4.src.value = '10.1.1.1'
        ipv4.dst.value = '10.1.1.2'
        ipv4.priority.dscp.phb.value = i * 8
        flow.duration.fixed_packets.packets = packets
        flow.duration.fixed_packets.delay = 10**9
        flow.duration.fixed_packets.delay_unit = 'nanoseconds'
        flow.size.fixed = size
        flow.rate.percentage = 10

    flow = config.flows.flow(name="rx_pause")[-1]
    flow.tx_rx.port.tx_name = rx.name
    flow.tx_rx.port.rx_name = tx.name
    flow.size.fixed = size
    flow.duration.fixed_seconds.delay = 20
    flow.rate.percentage = 100

    pfc = flow.packet.pfcpause()[-1]
    pfc.src.value = '00:AB:BC:AB:BC:AB'
    pfc.class_enable_vector.value = 'FF'
    pfc.control_op_code.value = '0101'
    for i in range(8):
        getattr(pfc, 'pause_class_%d' % i).value = 'FFFF'

    tr_state = api.transmit_state()
    tr_state.state = 'start'
    api.set_transmit_state(tr_state)
    utils.wait_for(
        lambda: results_ok(
            api, config, utils, size, packets, lossless_priorities
        ),
        'stats to be as expected', timeout_seconds=30
    )
    utils.wait_for(
        lambda: results_ok(api, config, utils, size, packets, []),
        'stats to be as expected', timeout_seconds=30
    )


def results_ok(api, cfg, utils, size, packets, lossless_priorities):
    """
    Returns true if stats are as expected, false otherwise.
    """
    port_results, flow_results = utils.get_all_stats(api)

    ok = [False, False, False, False, False, False, False, False, False]

    port_tx = sum(
        [p.frames_tx for p in port_results if p.name == 'raw_tx']
    )
    ok[8] = port_tx == packets * (8 - len(lossless_priorities))

    for f in flow_results:
        if f.name == 'rx_pause':
            continue

        _, p = f.name.split('tx_p')
        p = int(p)
        if p in lossless_priorities:
            ok[p] = f.frames_rx == 0
        else:
            ok[p] = f.frames_rx == packets

    return all(ok)
