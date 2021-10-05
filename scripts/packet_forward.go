// Steps to get started with this test
// - Ensure Go is installed on your system
// - mkdir -p scratch && cd scratch
// - curl -kLO https://raw.githubusercontent.com/open-traffic-generator/snappi-tests/main/scripts/packet_forward.go
// - go mod init example/test
// - go get github.com/open-traffic-generator/snappi/gosnappi@v0.6.3
// - go run packet_forward.go
// Open any new issues (or search for existing) at:
// - https://github.com/open-traffic-generator/openapiart/issues (specific to code generation)
// - https://github.com/open-traffic-generator/snappi/issues (anything related to OTG, apart from code generation)

package main

import (
	"fmt"
	"log"
	"time"

	"github.com/open-traffic-generator/snappi/gosnappi"
)

func main() {
	api := gosnappi.NewApi()
	if httpTransport := false; httpTransport {
		log.Println("Using HTTP transport ...")
		api.NewHttpTransport().SetLocation("https://ixia-c-service:443")
	} else {
		log.Println("Using gRPC transport ...")
		api.NewGrpcTransport().SetLocation("grpc-service.ixia-c:40051")
	}

	log.Println("Setting config ...")
	config := PacketForwardConfig(api)
	warn, err := api.SetConfig(config)
	LogWarnErr(warn, err)

	warn, err = api.SetProtocolState(api.NewProtocolState().SetState(gosnappi.ProtocolStateState.START))
	LogWarnErr(warn, err)

	err = WaitFor(func() (bool, error) {
		req := api.NewMetricsRequest()
		req.Bgpv4()
		res, err := api.GetMetrics(req)
		if err != nil {
			return false, err
		}

		log.Println("\n" + res.ToYaml())
		for _, row := range res.Bgpv4Metrics().Items() {
			if row.RoutesReceived() != 4 {
				return false, nil
			}
		}
		return true, nil
	}, "bgpv4 metrics to be ok")
	LogWarnErr(nil, err)

	log.Println("Starting transmit ...")
	ts := api.NewTransmitState().SetState(gosnappi.TransmitStateState.START)
	warn, err = api.SetTransmitState(ts)
	LogWarnErr(warn, err)

	err = WaitFor(func() (bool, error) {
		req := api.NewMetricsRequest()
		req.Flow()
		res, err := api.GetMetrics(req)
		if err != nil {
			return false, err
		}

		log.Println("\n" + res.ToYaml())
		for _, row := range res.FlowMetrics().Items() {
			if row.FramesRx() != 1000 {
				return false, nil
			}
		}
		return true, nil
	}, "flow metrics to be ok")
	LogWarnErr(nil, err)
}

func PacketForwardConfig(api gosnappi.GosnappiApi) gosnappi.Config {

	config := api.NewConfig()

	// add ports
	p1 := config.Ports().Add().SetName("p1").SetLocation("service-ixia-c-port1.ixia-c:5555+service-ixia-c-port1.ixia-c:50071")
	p2 := config.Ports().Add().SetName("p2").SetLocation("service-ixia-c-port2.ixia-c:5555+service-ixia-c-port2.ixia-c:50071")
	p3 := config.Ports().Add().SetName("p3").SetLocation("service-ixia-c-port3.ixia-c:5555+service-ixia-c-port3.ixia-c:50071")

	// add devices
	d1 := config.Devices().Add().SetName("d1")
	d2 := config.Devices().Add().SetName("d2")
	d3 := config.Devices().Add().SetName("d3")

	// add flows and common properties
	for i := 1; i <= 4; i++ {
		flow := config.Flows().Add()
		flow.Metrics().SetEnable(true)
		flow.Duration().FixedPackets().SetPackets(1000)
		flow.Rate().SetPps(500)
	}

	// add protocol stacks for device d1
	d1Eth := d1.Ethernets().Add().
		SetName("d1Eth").
		SetPortName(p1.Name()).
		SetMac("00:00:01:01:01:01").
		SetMtu(1500)

	d1Ip := d1Eth.Ipv4Addresses().Add().
		SetName("d1Ip").
		SetAddress("1.1.1.1").
		SetGateway("1.1.1.2").
		SetPrefix(24)

	d1Bgp := d1.Bgp().SetRouterId("1.1.1.1")
	d1BgpIfc := d1Bgp.Ipv4Interfaces().Add().SetIpv4Name(d1Ip.Name())
	d1BgpPeer := d1BgpIfc.Peers().Add().
		SetName("d1Bgp").
		SetPeerAddress("1.1.1.2").
		SetAsNumber(1111).
		SetAsType(gosnappi.BgpV4PeerAsType.EBGP)

	d1BgpRoute := d1BgpPeer.V4Routes().Add().
		SetName("d1BgpRoute").
		SetNextHopIpv4Address("1.1.1.1")

	d1BgpRoute.Addresses().Add().
		SetAddress("10.10.10.0").
		SetPrefix(24).
		SetCount(2).
		SetStep(2)

	d1BgpRoute.Communities().Add().
		SetAsNumber(1).
		SetAsCustom(2).
		SetType(gosnappi.BgpCommunityType.MANUAL_AS_NUMBER)

	d1BgpRoute.AsPath().
		SetAsSetMode(gosnappi.BgpAsPathAsSetMode.INCLUDE_AS_SET)

	d1BgpRoute.AsPath().Segments().Add().
		SetAsNumbers([]int64{1112, 1113}).
		SetType(gosnappi.BgpAsPathSegmentType.AS_SEQ)

	d1BgpRoute.Advanced().
		SetMultiExitDiscriminator(50).
		SetOrigin(gosnappi.BgpRouteAdvancedOrigin.EGP)

	// add protocol stacks for device d2
	d2Eth := d2.Ethernets().Add().
		SetName("d2Eth").
		SetPortName(p2.Name()).
		SetMac("00:00:02:02:02:02").
		SetMtu(1500)

	d2Ip := d2Eth.Ipv4Addresses().Add().
		SetName("d2Ip").
		SetAddress("2.2.2.2").
		SetGateway("2.2.2.1").
		SetPrefix(24)

	d2Bgp := d2.Bgp().SetRouterId("2.2.2.2")
	d2BgpIfc := d2Bgp.Ipv4Interfaces().Add().SetIpv4Name(d2Ip.Name())
	d2BgpPeer := d2BgpIfc.Peers().Add().
		SetName("d2Bgp").
		SetPeerAddress("2.2.2.1").
		SetAsNumber(2222).
		SetAsType(gosnappi.BgpV4PeerAsType.EBGP)

	d2BgpRoute := d2BgpPeer.V4Routes().Add().
		SetName("d2BgpRoute").
		SetNextHopIpv4Address("2.2.2.2")

	d2BgpRoute.Addresses().Add().
		SetAddress("20.20.20.0").
		SetPrefix(24).
		SetCount(2).
		SetStep(2)

	d2BgpRoute.Communities().Add().
		SetAsNumber(100).
		SetAsCustom(2).
		SetType(gosnappi.BgpCommunityType.MANUAL_AS_NUMBER)

	d2BgpRoute.AsPath().
		SetAsSetMode(gosnappi.BgpAsPathAsSetMode.INCLUDE_AS_SET)

	d2BgpRoute.AsPath().Segments().Add().
		SetAsNumbers([]int64{2223, 2224, 2225}).
		SetType(gosnappi.BgpAsPathSegmentType.AS_SEQ)

	d2BgpRoute.Advanced().
		SetMultiExitDiscriminator(40).
		SetOrigin(gosnappi.BgpRouteAdvancedOrigin.EGP)

	// add protocol stacks for device d3
	d3Eth := d3.Ethernets().Add().
		SetName("d3Eth").
		SetPortName(p3.Name()).
		SetMac("00:00:03:03:03:02").
		SetMtu(1500)

	d3Ip := d3Eth.Ipv4Addresses().Add().
		SetName("d3Ip").
		SetAddress("3.3.3.2").
		SetGateway("3.3.3.1").
		SetPrefix(24)

	d3Bgp := d3.Bgp().SetRouterId("3.3.3.2")
	d3BgpIfc := d3Bgp.Ipv4Interfaces().Add().SetIpv4Name(d3Ip.Name())
	d3BgpPeer := d3BgpIfc.Peers().Add().
		SetName("d3Bgp").
		SetPeerAddress("3.3.3.1").
		SetAsNumber(3332).
		SetAsType(gosnappi.BgpV4PeerAsType.EBGP)

	d3BgpRoute := d3BgpPeer.V4Routes().Add().
		SetName("d3BgpRoute").
		SetNextHopIpv4Address("3.3.3.2")

	d3BgpRoute.Addresses().Add().
		SetAddress("30.30.30.0").
		SetPrefix(24).
		SetCount(2).
		SetStep(2)

	d3BgpRoute.Communities().Add().
		SetAsNumber(1).
		SetAsCustom(2).
		SetType(gosnappi.BgpCommunityType.MANUAL_AS_NUMBER)

	d3BgpRoute.AsPath().
		SetAsSetMode(gosnappi.BgpAsPathAsSetMode.INCLUDE_AS_SET)

	d3BgpRoute.AsPath().Segments().Add().
		SetAsNumbers([]int64{3333, 3334}).
		SetType(gosnappi.BgpAsPathSegmentType.AS_SEQ)

	d3BgpRoute.Advanced().
		SetMultiExitDiscriminator(33).
		SetOrigin(gosnappi.BgpRouteAdvancedOrigin.EGP)

	// add endpoints and packet description flow 1
	f1 := config.Flows().Items()[0]
	f1.SetName(p1.Name() + " -> " + p2.Name()).
		TxRx().Device().
		SetTxNames([]string{d1BgpRoute.Name()}).
		SetRxNames([]string{d2BgpRoute.Name()})

	f1Eth := f1.Packet().Add().Ethernet()
	f1Eth.Src().SetValue(d1Eth.Mac())
	f1Eth.Dst().SetValue("00:00:00:00:00:00")

	f1Ip := f1.Packet().Add().Ipv4()
	f1Ip.Src().SetValue("10.10.10.1")
	f1Ip.Dst().SetValue("20.20.20.1")

	// add endpoints and packet description flow 2
	f2 := config.Flows().Items()[1]
	f2.SetName(p1.Name() + " -> " + p3.Name()).
		TxRx().Device().
		SetTxNames([]string{d1BgpRoute.Name()}).
		SetRxNames([]string{d3BgpRoute.Name()})

	f2Eth := f2.Packet().Add().Ethernet()
	f2Eth.Src().SetValue(d1Eth.Mac())
	f2Eth.Dst().SetValue("00:00:00:00:00:00")

	f2Ip := f2.Packet().Add().Ipv4()
	f2Ip.Src().SetValue("10.10.10.1")
	f2Ip.Dst().SetValue("30.30.30.1")

	// add endpoints and packet description flow 3
	f3 := config.Flows().Items()[2]
	f3.SetName(p2.Name() + " -> " + p1.Name()).
		TxRx().Device().
		SetTxNames([]string{d2BgpRoute.Name()}).
		SetRxNames([]string{d1BgpRoute.Name()})

	f3Eth := f3.Packet().Add().Ethernet()
	f3Eth.Src().SetValue(d2Eth.Mac())
	f3Eth.Dst().SetValue("00:00:00:00:00:00")

	f3Ip := f3.Packet().Add().Ipv4()
	f3Ip.Src().SetValue("20.20.20.1")
	f3Ip.Dst().SetValue("10.10.10.1")

	// add endpoints and packet description flow 4
	f4 := config.Flows().Items()[3]
	f4.SetName(p3.Name() + " -> " + p1.Name()).
		TxRx().Device().
		SetTxNames([]string{d3BgpRoute.Name()}).
		SetRxNames([]string{d1BgpRoute.Name()})

	f4Eth := f4.Packet().Add().Ethernet()
	f4Eth.Src().SetValue(d3Eth.Mac())
	f4Eth.Dst().SetValue("00:00:00:00:00:00")

	f4Ip := f4.Packet().Add().Ipv4()
	f4Ip.Src().SetValue("30.30.30.1")
	f4Ip.Dst().SetValue("10.10.10.1")

	log.Println(config.ToYaml())
	return config
}

func LogWarnErr(warn gosnappi.ResponseWarning, err error) {
	if err != nil {
		log.Printf("ERROR: %v\n", err)
	} else if warn != nil {
		for _, w := range warn.Warnings() {
			log.Printf("WARNING: %v\n", w)
		}
	}
}

func WaitFor(fn func() (bool, error), condition string) error {
	start := time.Now()
	log.Printf("Waiting for %s ...\n", condition)

	for {
		done, err := fn()
		if err != nil {
			return fmt.Errorf("error waiting for %s: %v", condition, err)
		}
		if done {
			log.Printf("Done waiting for %s\n", condition)
			return nil
		}

		if time.Since(start) > 30*time.Second {
			return fmt.Errorf("timeout occurred while waiting for %s", condition)
		}
		time.Sleep(500 * time.Millisecond)
	}
}
