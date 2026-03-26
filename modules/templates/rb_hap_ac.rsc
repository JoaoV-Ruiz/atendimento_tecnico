/interface bridge
add fast-forward=no name=bridge1
/interface ethernet
set [ find default-name=ether1 ] comment="1-LAN"
set [ find default-name=ether2 ] comment="2-WAN"
set [ find default-name=ether3 ] comment="3-LAN"
set [ find default-name=ether4 ] comment="4-LAN"
set [ find default-name=ether5 ] comment="5-LAN"
/interface pppoe-client
add add-default-route=yes disabled=no interface=ether2 keepalive-timeout=60 name=pppoe-out1 password=XXXSENHAPPPOEXXX use-peer-dns=yes user=XXXUSUARIOPPPOEXXX
/interface wireless security-profiles
set [ find default=yes ] supplicant-identity=MikroTik
add authentication-types=wpa-psk,wpa2-psk eap-methods="" management-protection=allowed mode=dynamic-keys name=profile1 supplicant-identity="" wpa-pre-shared-key=XXXWIFI_PASSXXX wpa2-pre-shared-key=XXXWIFI_PASSXXX
/interface wireless
set [ find default-name=wlan1 ] antenna-gain=0 band=2ghz-b/g/n channel-width=20/40mhz-Ce country=brazil disabled=yes mode=ap-bridge name=wlan1-24 security-profile=profile1 ssid=XXXWIFI_NAMEXXX station-roaming=enabled wireless-protocol=802.11 \
wps-mode=disabled
set [ find default-name=wlan2 ] antenna-gain=0 band=5ghz-a/n/ac channel-width=20/40/80mhz-Ceee country=brazil disabled=yes mode=ap-bridge name=wlan2-5 security-profile=profile1 ssid=XXXWIFI_5GHZ_NAMEXXX station-roaming=enabled wireless-protocol=802.11 \
wps-mode=disabled
/ip pool
add name=dhcp_pool0 ranges=192.168.8.2-192.168.8.200
/ip dhcp-server
add address-pool=dhcp_pool0 disabled=no interface=bridge1 name=dhcp1
/snmp community
set [ find default=yes ] addresses=177.53.64.20/32,172.20.12.0/24,172.20.5.91/32
/user group
set full policy=local,telnet,ssh,ftp,reboot,read,write,policy,test,winbox,password,web,sniff,sensitive,api,romon,dude,tikapp
/ip address
add address=192.168.8.1/24 interface=bridge1 network=192.168.8.0
/ip dhcp-server network
add address=192.168.8.0/24 dns-server=191.5.216.90,191.5.217.90 gateway=192.168.8.1
/ip firewall nat
add action=masquerade chain=srcnat out-interface=pppoe-out1 src-address=192.168.8.0/24
/ip service
set telnet address=177.53.64.20/32,10.254.254.2/32
set www address=177.53.64.20/32,10.254.254.2/32,192.168.8.0/24
set winbox address=177.53.64.20/32,10.254.254.2/32
/ip service disable numbers=1,3,4,5,7
/ip service set numbers=0,2,6 address=177.53.64.20,10.254.254.2,192.168.8.0/24
/tool graphing interface
add allow-address=177.53.64.20/32
add allow-address=10.254.254.2/32
/radius
add address=172.20.17.50 secret=CTHKGG335014daemeu service=login
/radius incoming
set accept=yes
/snmp
set contact=OSIRNET enabled=yes location=Pelotas/Rs
/system clock
set time-zone-autodetect=no time-zone-name=America/Sao_Paulo
/system identity
set name="XXXCOD_NOMEXXX"
/system scheduler
add interval=1d name=Backup-FTP on-event=Backup-FTP policy=ftp,reboot,read,write,policy,test,password,sniff,sensitive start-date=jan/01/1970 start-time=05:00:00
/system script
add dont-require-permissions=no name=Backup-FTP owner=rodrigo policy=ftp,reboot,read,write,policy,test,password,sniff,sensitive source="# Set local variables. Change the value in \"\" to reflect your environment.\r\
\n\r\
\n:global name=backupfile value=([/system identity get name] . \"-\" . [/system clock get time])\r\
\n:local hostname \"\$backupfile\";\r\
\n:local password \"@Cliente2019\"\r\
\n:local username \"cliente\"\r\
\n:local ftpserver \"172.20.1.62\"\r\
\n\r\
\n# Set Filename variables. Do not change this unless you want to edit the format of the filename.\r\
\n\r\
\n:local time [/system clock get time];\r\
\n:local date ([:pick [/system clock get date] 0 3] \\\r\
\n. [:pick [/system clock get date] 4 6] \\\r\
\n. [:pick [/system clock get date] 7 11]);\r\
\n:local filename \"\$hostname-\$date-\$time\";\r\
\n\r\
\n# Create backup file and export the config.\r\
\n\r\
\nexport compact file=\"\$filename\"\r\
\n/system backup save name=\"\$filename\"\r\
\n\r\
\n:log info \"Backup Created Successfully\"\r\
\n\r\
\n# Upload config file to FTP server.\r\
\n\r\
\n/tool fetch address=\$ftpserver src-path=\"\$filename.rsc\" \\\r\
\nuser=\$username mode=ftp password=\$password \\\r\
\ndst-path=\"\$filename.rsc\" upload=yes\r\
\n\r\
\n# Upload backup file to FTP server.\r\
\n\r\
\n/tool fetch address=\$ftpserver src-path=\"\$filename.backup\" \\\r\
\nuser=\$username mode=ftp password=\$password \\\r\
\ndst-path=\"\$filename.backup\" upload=yes\r\
\n\r\
\n:log info \"Backup Uploaded Successfully\"\r\
\n\r\
\n# Delete created backup files once they have been uploaded\r\
\n# so they don't accumulate and fill up storage space on the router.\r\
\n\r\
\n/file remove \"\$filename.rsc\"\r\
\n/file remove \"\$filename.backup\"\r\
\n\r\
\n:log info \"Local Backup Files Deleted Successfully\""
/user aaa
set default-group=full use-radius=yes
/user
add disable=no group=full name=tecnico password=051rn3tt3c
remove admin
/interface bridge port
add bridge=bridge1 interface=ether1
add bridge=bridge1 interface=ether3
add bridge=bridge1 interface=ether4
add bridge=bridge1 interface=ether5
add bridge=bridge1 interface=wlan1-24
add bridge=bridge1 interface=wlan2-5
/