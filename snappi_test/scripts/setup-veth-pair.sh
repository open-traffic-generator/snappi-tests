#!/bin/sh

set -e

if [ "$USER" != "root" ]
  then echo "Please execute this script as sudo"
  exit
fi

if [ "${#}" != "2" ]
    then echo "usage: ${0} <name of ifc1> <name of ifc2>"
    exit
fi

IFC1=$1
IFC2=$2

ip link add ${IFC1} type veth peer name ${IFC2}
ip link set ${IFC1} up
ip link set ${IFC2} up

echo "veth pair ${IFC1} <-> ${IFC2} has been successfully set up"