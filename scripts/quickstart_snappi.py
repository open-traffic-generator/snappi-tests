import snappi
# create a new API instance where host points to controller
api = snappi.api(host='https://localhost')

# create a config object to be pushed to controller
config = api.config()
# add a port with location pointing to traffic engine
prt = config.ports.port(name='prt', location='localhost:5555')[-1]
# add a flow and assign endpoints
flw = config.flows.flow(name='flw')[-1]
flw.tx_rx.port.tx_name = prt.name

# configure 100 packets to be sent, each having a size of 128 bytes
flw.size.fixed = 128
flw.duration.fixed_packets.packets = 100

# add Ethernet, IP and TCP protocol headers with defaults
flw.packet.ethernet().ipv4().tcp()

# push configuration
api.set_config(config)

# start transmitting configured flows
ts = api.transmit_state()
ts.state = ts.START
api.set_transmit_state(ts)

# fetch & print port metrics
req = api.metrics_request()
req.port.port_names = [prt.name]
print(api.get_metrics(req))
