/interface bridge
add name=Bridge_EasyAuth
add name=Bridge_LAN
/interface ethernet
XXXLINHAS_ETHERNETXXX
/interface pppoe-client
add add-default-route=yes interface=ether2 keepalive-timeout=60 name=pppoe-out1 password=XXXSENHAPPPOEXXX use-peer-dns=yes user=XXXUSUARIOPPPOEXXX disable=no
/ip pool
add name=dhcp_pool1 ranges=192.168.8.2-192.168.8.200
/ip dhcp-server
add address-pool=dhcp_pool1 disabled=no interface=bridge1 name=dhcp1
/ip address
add address=192.168.8.1/24 interface=bridge1 network=192.168.8.0
/ip dhcp-server network
add address=192.168.8.0/24 dns-server=191.5.216.90,191.5.217.90 gateway=192.168.8.1
/interface vlan
XXXVLAN_1750_DINAMICAXXX
add interface=ether2 name=Vlan1751_UPLINK vlan-id=1751
XXXVLAN_1751_DINAMICAXXX
/snmp community
set [ find default=yes ] addresses=177.53.64.20/32,172.20.5.91/32,172.20.12.0/24
/interface bridge port
XXXLINHAS_BRIDGEXXX
add bridge=Bridge_EasyAuth interface=Vlan1751_UPLINK
XXXLINHAS_BRIDGE_DINAMICAXXX
/ip firewall address-list
add address=170.79.75.22 comment=Casa_Vinicios list=Confiaveis
add address=177.53.64.20 comment=Empresa_Osirnet list=Confiaveis
add address=177.66.24.128/26 comment=Aprimorar_SUP list=Confiaveis
add address=177.53.64.101 comment="TS Aprimorar" list=Confiaveis
add address=172.20.12.0/24 comment=ZABBIX list=Confiaveis
add address=172.20.5.91 comment="Servidor Zabbix" list=Monitoramento
add address=191.5.216.82 comment=Servidor_Zabbix list=Monitoramento
add address=172.20.12.0/24 comment="Faixa de Monitoramento" list=Monitoramento
add address=177.53.64.101 comment="TS Aprimorar" list=Monitoramento
add address=170.79.75.22 comment=Casa_Vinicios list=Monitoramento
add address=177.53.64.20 comment=Empresa_Osirnet list=Monitoramento
add address=172.20.23.74 comment="Servidor UISP" list=Monitoramento
/ip firewall filter
add action=accept chain=input comment="LIBERA ACESSO REMOTO DA RB" src-address-list=Confiaveis
add action=accept chain=input comment="LIBERA PING PARA A RB" protocol=icmp
add action=accept chain=input comment="LIBERA MONITORAMENTO POR SNMP" dst-port=161 protocol=udp src-address-list=Monitoramento
add action=accept chain=input comment="LIBERA NEIGHBORS" dst-port=5678 protocol=udp
add action=accept chain=input comment="LIBERA ACESSO MAC-TELNET" dst-port=20561 protocol=udp
add action=accept chain=input comment="LIBERA TUNEIS(EOIP, GRE...)" protocol=gre
add action=accept chain=input comment="LIBERA PACOTES OSPF" protocol=ospf
add action=accept chain=input comment="LIMITACAO DE 30 PINGS POR SEGUNDO" limit=30,5:packet protocol=icmp
add action=accept chain=input comment="LIBERA PACOTES DNS" protocol=udp src-port=53
add action=accept chain=input comment="LIBERA PACOTES DNS" protocol=tcp src-port=53
add action=accept chain=input comment="LIBERA PACOTES ESTABELECIDOS" connection-state=established
add action=accept chain=input comment="LIBERA PACOTES RELACIONADOS" connection-state=related
add action=log chain=input disabled=yes
add action=drop chain=input comment="BLOQUEIA TUDO QUE NAO ESTA LIBERADO NAS REGRAS ACIMA" disabled=yes log-prefix=drop
/ip firewall nat

pppoe-out1 not ready
add action=masquerade chain=srcnat out-interface=pppoe-out1
/ip service
set telnet disabled=yes
set ftp disabled=yes
set www address=177.53.64.20/32
set ssh disabled=yes
set api disabled=yes
set winbox address=177.53.64.20/32
set api-ssl disabled=yes
/radius
add address=172.20.17.50 secret=CTHKGG335014daemeu service=login src-address=0.0.0.0
/radius incoming
set accept=yes
/snmp
set contact=Osirnet enabled=yes location=POP trap-target=0.0.0.0
/system clock
set time-zone-name=America/Sao_Paulo
/system identity
set name="XXXCOD_NOMEXXX"
/system note
set show-at-login=no
/system ntp client
set enabled=yes
/system scheduler
add interval=1d name=Backup-FTP on-event=Backup-FTP policy=ftp,reboot,read,write,policy,test,password,sniff,sensitive start-date=jan/01/1970 start-time=05:00:00
/system script
add dont-require-permissions=no name=Backup-FTP owner=rodrigo policy=ftp,reboot,read,write,policy,test,password,sniff,sensitive source="# Set local variables. Change the value in \"\" to reflect your environment.\r\
\n\r\
\n:global name=backupfile value=([/system identity get name] . \"-\" . [/system clock get time])\r\
\n:local hostname \"\$backupfile\";\r\
\n:local password \"3v3nt0s@051r\"\r\
\n:local username \"eventos\"\r\
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