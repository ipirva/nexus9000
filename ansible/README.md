nexus9000 with ansible - vxlan evpn underlay and overlay infrastructure

Fabric 1
#SN:SAL1830XABP -- n9k-spine-1

#SN:FDO20511MS6 -- n9k-leaf-1
#SN:FDO20441PZS -- n9k-leaf-2
#SN:FDO20400MVA -- n9k-leaf-3
#SN:FDO21050FUA -- n9k-leaf-4

#SN:FDO20371M2Z -- n9k-bleaf-1
#SN:FDO211120Q0 -- n9k-bgw-1 (Multi-Site)

Bring up Fabric 1
(~/ansible/fabric1)-(22 files, 100Kb)--> date; ansible-playbook -i /root/ansible/scripts/inventory.py ___bring_up_fabric.yml; date
Thu Sep 27 21:26:04 UTC 2018
PLAY RECAP ***************************************************************************************************************************************************
n9k-bgw-1                  : ok=68   changed=48   unreachable=0    failed=0
n9k-bleaf-1                : ok=78   changed=41   unreachable=0    failed=0
n9k-leaf-1                 : ok=76   changed=53   unreachable=0    failed=0
n9k-leaf-2                 : ok=76   changed=53   unreachable=0    failed=0
n9k-leaf-3                 : ok=76   changed=53   unreachable=0    failed=0
n9k-leaf-4                 : ok=76   changed=53   unreachable=0    failed=0
n9k-spine-1                : ok=40   changed=31   unreachable=0    failed=0
Thu Sep 27 21:31:49 UTC 2018


Fabric 2
#SN:FDO21201JVG -- n9k-spine-2
#SN:FDO210627TL -- n9k-leaf-5

#SN:FDO20370B9Q -- n9k-bleaf-3

#SN:FDO20340P41 -- n9k-bgw-2 (Multi-Site)
#SN:FDO210507CS -- n9k-bgw-3 (Multi-Site)

Bring up Fabric 2
(~/ansible/fabric2)-(22 files, 96Kb)--> date; ansible-playbook -i /root/ansible/scripts/inventory.py ___bring_up_fabric.yml;date
Thu Sep 27 21:41:16 UTC 2018
PLAY RECAP ***************************************************************************************************************************************************
n9k-bgw-2                  : ok=72   changed=52   unreachable=0    failed=0
n9k-bgw-3                  : ok=72   changed=52   unreachable=0    failed=0
n9k-bleaf-3                : ok=81   changed=44   unreachable=0    failed=0
n9k-leaf-5                 : ok=76   changed=39   unreachable=0    failed=0
n9k-spine-2                : ok=40   changed=31   unreachable=0    failed=0

Thu Sep 27 21:45:15 UTC 2018


export NXAPI_PSW=""
export SPARK_ROOM_ID=""
export SPARK_TOKEN=""

cd /tftpboot/scripts/tshoot/check_cabling/ && python /tftpboot/scripts/tshoot/check_cabling/checkcable.py SAL1830XABP /root/ansible/fabric1/connectivity.json lldp


/root/ansible/scripts/inventory.py --topology_file=/root/ansible/fabric1/topology.yml --connectivity_file=/root/ansible/fabric1/connectivity.json --write

Get facts:
ansible-playbook -i /root/ansible/scripts/inventory.py  check_connectivity.yml

Generate needed variables (underlay,overlay, vpc ...):
ansible-playbook -i /root/ansible/scripts/inventory.py generate_variables.yml
ansible-playbook -i /root/ansible/scripts/inventory.py generate_vpc_variables.yml

Activate needed features:
ansible-playbook -i /root/ansible/scripts/inventory.py configure_leaf_features.yml
ansible-playbook -i /root/ansible/scripts/inventory.py configure_spine_features.yml

Configure Underlay:
ansible-playbook -i /root/ansible/scripts/inventory.py configure_underlay.yml

Configure Overlay:
ansible-playbook -i /root/ansible/scripts/inventory.py configure_overlay.yml

Configure VPC:
ansible-playbook -i /root/ansible/scripts/inventory.py configure_vpc.yml

Save & Backup:
ansible-playbook -i /root/ansible/scripts/inventory.py save_and_backup_configuration.yml

Fabric2

cd /tftpboot/scripts/tshoot/check_cabling/ && python /tftpboot/scripts/tshoot/check_cabling/checkcable.py FDO21201JVG /root/ansible/fabric2/connectivity.json lldp

/root/ansible/scripts/inventory.py --topology_file=/root/ansible/fabric2/topology.yml --connectivity_file=/root/ansible/fabric2/connectivity.json --write

