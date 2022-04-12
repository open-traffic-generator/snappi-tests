package main

import (
	"log"
	"time"

	"github.com/open-traffic-generator/snappi/gosnappi"
)

// hostname and interfaces of ixia-c-one node from containerlab topology
const (
	otgHost  = "https://clab-ixia-c-ixia-c-one"
	otgPort1 = "eth1"
	otgPort2 = "eth2"
)

var (
	pktCount = 1000
	routeCount = int32(5)
)

func main() {

	api, config := newConfig()

	// push traffic configuration to otgHost
	res, err := api.SetConfig(config)
	checkResponse(res, err)

	// start protocol configured devices
	ps := api.NewProtocolState().
		SetState(gosnappi.ProtocolStateState.START)
	res, err = api.SetProtocolState(ps)
	checkResponse(res, err)

	// fetch Bgpv4 metrics and wait for sessions to be up and routes count to be correct
	mr := api.NewMetricsRequest()
	mr.Bgpv4()
	waitFor(
		func() bool {
			res, err := api.GetMetrics(mr)
			checkResponse(res, err)

			bgp1m := res.Bgpv4Metrics().Items()[0]
			bgp2m := res.Bgpv4Metrics().Items()[1]
			return bgp1m.SessionState() == "up" && bgp2m.SessionState() == "up" && bgp1m.RoutesAdvertised() == routeCount && bgp2m.RoutesAdvertised() == routeCount && bgp1m.RoutesReceived() == routeCount && bgp2m.RoutesReceived() == routeCount
		},
		10*time.Second,
	)

	// start transmitting configured flows
	ts := api.NewTransmitState().SetState(gosnappi.TransmitStateState.START)
	res, err = api.SetTransmitState(ts)
	checkResponse(res, err)

	// fetch flow metrics and wait for received frame count to be correct
	mr = api.NewMetricsRequest()
	mr.Flow()
	waitFor(
		func() bool {
			res, err := api.GetMetrics(mr)
			checkResponse(res, err)

			fm := res.FlowMetrics().Items()[0]
			return fm.Transmit() == gosnappi.FlowMetricTransmit.STOPPED && fm.FramesRx() == int64(pktCount)
		},
		10*time.Second,
	)
}

func checkResponse(res interface{}, err error) {
	if err != nil {
		log.Fatal(err)
	}
	switch v := res.(type) {
	case gosnappi.MetricsResponse:
		log.Printf("Metrics Response:\n%s\n", v)
	case gosnappi.ResponseWarning:
		for _, w := range v.Warnings() {
			log.Println("WARNING:", w)
		}
	default:
		log.Fatal("Unknown response type:", v)
	}
}

func newConfig() (gosnappi.GosnappiApi, gosnappi.Config) {
	// create a new API handle to make API calls against otgHost
	api := gosnappi.NewApi()
	api.NewHttpTransport().SetLocation(otgHost).SetVerify(false)

	// create an empty traffic configuration
	config := api.NewConfig()
	// create traffic endpoints
	p1 := config.Ports().Add().SetName("p1").SetLocation(otgPort1)
	p2 := config.Ports().Add().SetName("p2").SetLocation(otgPort2)

	// create devices
	p1d1 := config.Devices().Add().SetName("p1d1")
	p1d1Eth := p1d1.Ethernets().Add().
		SetName("p1d1eth").
		SetPortName(p1.Name()).
		SetMac("00:00:01:01:01:01")
	p1d1IPv4 := p1d1Eth.Ipv4Addresses().Add().
		SetName("p1d1Ipv4").
		SetAddress("1.1.1.2").
		SetGateway("1.1.1.1").
		SetPrefix(int32(24))

	p1d1BGP := p1d1.Bgp().
		SetRouterId(p1d1IPv4.Address())
	p1d1BGPv4Peer := p1d1BGP.Ipv4Interfaces().Add().
		SetIpv4Name(p1d1IPv4.Name()).
		Peers().Add().
		SetName("p1d1BGPv4Peer").
		SetPeerAddress(p1d1IPv4.Gateway()).
		SetAsNumber(int32(2222)).
		SetAsType(gosnappi.BgpV4PeerAsType.EBGP)

	p1d1BGPv4PeerRoutes := p1d1BGPv4Peer.V4Routes().Add().
		SetName("p1d1BGPv4PeerR1").
		SetNextHopIpv4Address(p1d1IPv4.Address()).
		SetNextHopAddressType(gosnappi.BgpV4RouteRangeNextHopAddressType.IPV4).
		SetNextHopMode(gosnappi.BgpV4RouteRangeNextHopMode.MANUAL)
	p1d1BGPv4PeerRoutes.Addresses().Add().
		SetAddress("10.10.10.1").
		SetPrefix(24).
		SetCount(5).
		SetStep(1)

	p2d1 := config.Devices().Add().SetName("p2d1")
	p2d1Eth := p2d1.Ethernets().Add().
		SetName("p2d1eth").
		SetPortName(p2.Name()).
		SetMac("00:00:02:02:02:02")
	p2d1IPv4 := p2d1Eth.Ipv4Addresses().Add().
		SetName("p2d1Ipv4").
		SetAddress("2.2.2.2").
		SetGateway("2.2.2.1").
		SetPrefix(int32(24))

	p2d1BGP := p2d1.Bgp().
		SetRouterId(p2d1IPv4.Address())
	p2d1BGPv4Peer := p2d1BGP.Ipv4Interfaces().Add().
		SetIpv4Name(p2d1IPv4.Name()).
		Peers().Add().
		SetName("p2d1BGPv4Peer").
		SetPeerAddress(p2d1IPv4.Gateway()).
		SetAsNumber(int32(3333)).
		SetAsType(gosnappi.BgpV4PeerAsType.EBGP)

	p2d1BGPv4PeerRoutes := p2d1BGPv4Peer.V4Routes().Add().
		SetName("p2d1BGPv4PeerR1").
		SetNextHopIpv4Address(p2d1IPv4.Address()).
		SetNextHopAddressType(gosnappi.BgpV4RouteRangeNextHopAddressType.IPV4).
		SetNextHopMode(gosnappi.BgpV4RouteRangeNextHopMode.MANUAL)
	p2d1BGPv4PeerRoutes.Addresses().Add().
		SetAddress("20.20.20.1").
		SetPrefix(24).
		SetCount(5).
		SetStep(1)

	// create a flow and set the endpoints
	f1 := config.Flows().Add().SetName("p1.v4.p2")

	f1.TxRx().Device().SetTxNames([]string{p1d1BGPv4PeerRoutes.Name()}).SetRxNames([]string{p2d1BGPv4PeerRoutes.Name()})

	// enable per flow metrics tracking
	f1.Metrics().SetEnable(true)
	// set size, count and transmit rate for all packets in the flow
	f1.Size().SetFixed(512)
	f1.Rate().SetPps(500)
	f1.Duration().FixedPackets().SetPackets(int32(pktCount))

	// configure headers for all packets in the flow
	eth := f1.Packet().Add().Ethernet()
	ip := f1.Packet().Add().Ipv4()

	eth.Src().SetValue("00:00:01:01:01:01")

	ip.Src().SetValue("10.10.10.1")
	ip.Dst().Increment().SetStart("20.20.20.1").SetStep("0.0.0.1").SetCount(5)

	log.Printf("OTG configuration:\n%s\n", config)
	return api, config
}

func waitFor(fn func() bool, timeout time.Duration) {
	start := time.Now()
	for {
		if fn() {
			return
		}
		if time.Since(start) > timeout {
			log.Fatal("Timeout occurred !")
		}

		time.Sleep(500 * time.Millisecond)
	}
}