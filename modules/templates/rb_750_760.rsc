/interface bridge
add name=bridge1
/interface ethernet
set [ find default-name=ether1 ] comment="1-LAN"
set [ find default-name=ether2 ] comment="2-WAN"
set [ find default-name=ether3 ] comment="3-LAN"
set [ find default-name=ether4 ] comment="4-LAN"
set [ find default-name=ether5 ] comment="5-LAN"
/interface pppoe-client
add add-default-route=yes disabled=no interface=ether2 max-mru=1500 max-mtu=1500 name=pppoe-out1 password=XXXSENHAPPPOEXXX \
use-peer-dns=yes user=XXXUSUARIOPPPOEXXX
/ip pool
add name=dhcp_pool1 ranges=192.168.8.2-192.168.8.200
/ip dhcp-server
add address-pool=dhcp_pool1 disabled=no interface=bridge1 name=dhcp1
/ip address
add address=192.168.8.1/24 interface=bridge1 network=192.168.8.0
/ip dhcp-server network
add address=192.168.8.0/24 dns-server=191.5.216.90,191.5.217.90 gateway=192.168.8.1
/ip firewall nat
add action=masquerade chain=srcnat out-interface=pppoe-out1
/ip service
set telnet address=177.53.64.20/32,10.254.254.2/32,192.168.8.0/24
set ftp disabled=yes
set www address=177.53.64.20/32,10.254.254.2/32,192.168.8.0/24
set ssh port=222 disabled=no address=177.53.64.20,10.254.254.2,192.168.8.0/24
set api disabled=yes
set winbox address=177.53.64.20/32,10.254.254.2/32,192.168.8.0/24
set api-ssl disabled=yes
/snmp
set contact=Osirnet enabled=yes location=Pelotas/RS
/snmp community
set [ find default=yes ] addresses=177.53.64.20/32,172.20.12.0/24,172.20.5.91/32
/user
add disable=no group=read name=zabbixppp password=zabbix@t1k
/tool graphing interface
add allow-address=177.53.64.20/32
add allow-address=10.254.254.2/32
/user aaa set default-group=full use-radius=yes
/radius
add address=172.20.17.50 secret=CTHKGG335014daemeu service=login
/radius incoming
set accept=yes
/system clock
set time-zone-name=America/Manaus
/system identity
set name="XXXCOD_NOMEXXX"
/system routerboard settings
set boot-device=flash-boot cpu-frequency=650MHz protected-routerboot=disabled
/user
add disable=no group=full name=tecnico password=051rn3tt3c
remove admin
/interface bridge port
add bridge=bridge1 interface=ether1
add bridge=bridge1 interface=ether3
add bridge=bridge1 interface=ether4
add bridge=bridge1 interface=ether5
/