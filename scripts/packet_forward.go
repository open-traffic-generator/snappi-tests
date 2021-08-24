package main

import (
	"log"

	// tested with github.com/open-traffic-generator/snappi/gosnappi@v0.4.36
	"github.com/open-traffic-generator/snappi/gosnappi"
)

func main() {

	gosnappi.StartMockServer("localhost:50001")

	api := gosnappi.NewApi()
	api.NewGrpcTransport().SetLocation("localhost:50001")
	config := PacketForwardConfig(api)

	if true {
		_, err := api.SetConfig(config)
		if err != nil {
			log.Fatal(err)
		}

		req := api.NewMetricsRequest()
		req.Bgpv4()
		for i := 0; i < 10; i++ {
			res, err := api.GetMetrics(req)
			if err != nil {
				log.Fatal(err)
			}

			// TODO: cannot extract further from response
			log.Println(res)
		}
	}
}

func PacketForwardConfig(api gosnappi.GosnappiApi) gosnappi.Config {

	config := api.NewConfig()

	// add ports
	p1 := config.Ports().Add().SetName("p1").SetLocation("service-ixia-c-port1.ixia-c")
	p2 := config.Ports().Add().SetName("p2").SetLocation("service-ixia-c-port2.ixia-c")
	p3 := config.Ports().Add().SetName("p3").SetLocation("service-ixia-c-port3.ixia-c")

	// add devices
	d1 := config.Devices().Add().SetName("d1").SetContainerName(p1.Name())
	d2 := config.Devices().Add().SetName("d2").SetContainerName(p2.Name())
	d3 := config.Devices().Add().SetName("d3").SetContainerName(p3.Name())

	// add flows and common properties
	for i := 1; i <= 4; i++ {
		flow := config.Flows().Add()
		flow.Metrics().SetEnable(true)
		flow.Duration().FixedPackets().SetPackets(1000)
		flow.Rate().SetPps(500)
	}

	// add protocol stacks for device d1
	d1Eth := d1.Ethernet().
		SetName("d1Eth").
		SetMac("00:00:01:01:01:01").
		SetMtu(1500)

	d1Eth.Vlans().Add().
		SetName("d1Vlan").
		SetId(100)

	d1Ip := d1Eth.Ipv4().
		SetName("d1Ip").
		SetAddress("1.1.1.1").
		SetGateway("1.1.1.2").
		SetPrefix(24)

	d1Bgp := d1Ip.Bgpv4().
		SetName("d1Bgp").
		SetDutAddress("1.1.1.2").
		SetRouterId("1.1.1.1").
		SetAsNumber(1111).
		SetAsType(gosnappi.DeviceBgpv4AsType.EBGP)

	d1BgpRoute := d1Bgp.Bgpv4Routes().Add().
		SetName("d1BgpRoute").
		SetNextHopAddress("1.1.1.1")

	d1BgpRoute.Addresses().Add().
		SetAddress("10.10.10.0").
		SetPrefix(24).
		SetCount(2).
		SetStep(2)

	d1BgpRoute.Communities().Add().
		SetAsNumber(1).
		SetAsCustom(2).
		SetCommunityType(gosnappi.DeviceBgpCommunityCommunityType.MANUAL_AS_NUMBER)

	d1BgpRoute.AsPath().
		SetOverridePeerAsSetMode(true).
		SetAsSetMode(gosnappi.DeviceBgpAsPathAsSetMode.INCLUDE_AS_SET)

	d1BgpRoute.AsPath().AsPathSegments().Add().
		SetAsNumbers([]int32{1112, 1113}).
		SetSegmentType(gosnappi.DeviceBgpAsPathSegmentSegmentType.AS_SEQ)

	d1BgpRoute.Advanced().
		SetMultiExitDiscriminator(50).
		SetOrigin(gosnappi.DeviceBgpRouteAdvancedOrigin.EGP)

	// add protocol stacks for device d2
	d2Eth := d2.Ethernet().
		SetName("d2Eth").
		SetMac("00:00:02:02:02:02").
		SetMtu(1500)

	d2Eth.Vlans().Add().
		SetName("d2Vlan").
		SetId(200)

	d2Ip := d2Eth.Ipv4().
		SetName("d2Ip").
		SetAddress("2.2.2.2").
		SetGateway("2.2.2.1").
		SetPrefix(24)

	d2Bgp := d2Ip.Bgpv4().
		SetName("d2Bgp").
		SetDutAddress("2.2.2.1").
		SetRouterId("2.2.2.2").
		SetAsNumber(2222).
		SetAsType(gosnappi.DeviceBgpv4AsType.EBGP)

	d2BgpRoute := d2Bgp.Bgpv4Routes().Add().
		SetName("d2BgpRoute").
		SetNextHopAddress("2.2.2.2")

	d2BgpRoute.Addresses().Add().
		SetAddress("20.20.20.0").
		SetPrefix(24).
		SetCount(2).
		SetStep(2)

	d2BgpRoute.Communities().Add().
		SetAsNumber(100).
		SetAsCustom(2).
		SetCommunityType(gosnappi.DeviceBgpCommunityCommunityType.MANUAL_AS_NUMBER)

	d2BgpRoute.AsPath().
		SetOverridePeerAsSetMode(true).
		SetAsSetMode(gosnappi.DeviceBgpAsPathAsSetMode.INCLUDE_AS_SET)

	d2BgpRoute.AsPath().AsPathSegments().Add().
		SetAsNumbers([]int32{2223, 2224, 2225}).
		SetSegmentType(gosnappi.DeviceBgpAsPathSegmentSegmentType.AS_SEQ)

	d2BgpRoute.Advanced().
		SetMultiExitDiscriminator(40).
		SetOrigin(gosnappi.DeviceBgpRouteAdvancedOrigin.EGP)

	// add protocol stacks for device d3
	d3Eth := d3.Ethernet().
		SetName("d3Eth").
		SetMac("00:00:03:03:03:02").
		SetMtu(1500)

	d3Eth.Vlans().Add().
		SetName("d3Vlan").
		SetId(300)

	d3Ip := d3Eth.Ipv4().
		SetName("d3Ip").
		SetAddress("3.3.3.2").
		SetGateway("3.3.3.1").
		SetPrefix(24)

	d3Bgp := d3Ip.Bgpv4().
		SetName("d3Bgp").
		SetDutAddress("3.3.3.1").
		SetRouterId("3.3.3.2").
		SetAsNumber(3332).
		SetAsType(gosnappi.DeviceBgpv4AsType.EBGP)

	d3BgpRoute := d3Bgp.Bgpv4Routes().Add().
		SetName("d3BgpRoute").
		SetNextHopAddress("3.3.3.2")

	d3BgpRoute.Addresses().Add().
		SetAddress("30.30.30.0").
		SetPrefix(24).
		SetCount(2).
		SetStep(2)

	d3BgpRoute.Communities().Add().
		SetAsNumber(1).
		SetAsCustom(2).
		SetCommunityType(gosnappi.DeviceBgpCommunityCommunityType.MANUAL_AS_NUMBER)

	d3BgpRoute.AsPath().
		SetOverridePeerAsSetMode(true).
		SetAsSetMode(gosnappi.DeviceBgpAsPathAsSetMode.INCLUDE_AS_SET)

	d3BgpRoute.AsPath().AsPathSegments().Add().
		SetAsNumbers([]int32{3333, 3334}).
		SetSegmentType(gosnappi.DeviceBgpAsPathSegmentSegmentType.AS_SEQ)

	d3BgpRoute.Advanced().
		SetMultiExitDiscriminator(33).
		SetOrigin(gosnappi.DeviceBgpRouteAdvancedOrigin.EGP)

	// add endpoints and packet description flow 1
	f1 := config.Flows().Items()[0]
	f1.SetName(p1.Name() + " -> " + p2.Name()).
		TxRx().Port().SetTxName(p1.Name()).SetRxName(p2.Name())

	f1Eth := f1.Packet().Add().Ethernet()
	f1Eth.Src().SetValue(d1Eth.Mac())

	f1Vlan := f1.Packet().Add().Vlan()
	f1Vlan.Id().SetValue(d1Eth.Vlans().Items()[0].Id())
	f1Vlan.Tpid().SetValue(33024)

	f1Ip := f1.Packet().Add().Ipv4()
	f1Ip.Src().SetValue("10.10.10.1")
	f1Ip.Dst().SetValue("20.20.20.1")

	// add endpoints and packet description flow 2
	f2 := config.Flows().Items()[1]
	f2.
		SetName(p1.Name() + " -> " + p3.Name()).
		TxRx().Port().SetTxName(p1.Name()).SetRxName(p3.Name())

	f2Eth := f2.Packet().Add().Ethernet()
	f2Eth.Src().SetValue(d1Eth.Mac())

	f2Vlan := f2.Packet().Add().Vlan()
	f2Vlan.Id().SetValue(d1Eth.Vlans().Items()[0].Id())
	f2Vlan.Tpid().SetValue(33024)

	f2Ip := f2.Packet().Add().Ipv4()
	f2Ip.Src().SetValue("10.10.10.1")
	f2Ip.Dst().SetValue("30.30.30.1")

	// add endpoints and packet description flow 3
	f3 := config.Flows().Items()[2]
	f3.
		SetName(p2.Name() + " -> " + p1.Name()).
		TxRx().Port().SetTxName(p2.Name()).SetRxName(p1.Name())

	f3Eth := f3.Packet().Add().Ethernet()
	f3Eth.Src().SetValue(d2Eth.Mac())

	f3Vlan := f3.Packet().Add().Vlan()
	f3Vlan.Id().SetValue(d2Eth.Vlans().Items()[0].Id())
	f3Vlan.Tpid().SetValue(33024)

	f3Ip := f3.Packet().Add().Ipv4()
	f3Ip.Src().SetValue("20.20.20.1")
	f3Ip.Dst().SetValue("10.10.10.1")

	// add endpoints and packet description flow 4
	f4 := config.Flows().Items()[3]
	f4.
		SetName(p3.Name() + " -> " + p1.Name()).
		TxRx().Port().SetTxName(p3.Name()).SetRxName(p1.Name())

	f4Eth := f4.Packet().Add().Ethernet()
	f4Eth.Src().SetValue(d3Eth.Mac())

	f4Vlan := f4.Packet().Add().Vlan()
	f4Vlan.Id().SetValue(d3Eth.Vlans().Items()[0].Id())
	f4Vlan.Tpid().SetValue(33024)

	f4Ip := f4.Packet().Add().Ipv4()
	f4Ip.Src().SetValue("30.30.30.1")
	f4Ip.Dst().SetValue("10.10.10.1")

	log.Println(config.ToYaml())
	return config
}
