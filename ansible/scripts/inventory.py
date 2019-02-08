#!/usr/bin/env python
'''
ipirva july 2018
generate inventory from the cabling connectivity file
generate topology.yml from the cabling connectivity file
'''
'''
connectivity.json
/tftpboot/scripts/tshoot/check_cabling/connectivity.json
'''
import json
import yaml
import re
import sys
import os

# current directory
wdir = os.getcwd()
 
if len(sys.argv) <= 1:
    help = """
Please use one of the following arguments:
--list - inventory list (Ansible uses this option by default)
--topology - show topology details
--write - write topology details on disk
and specify the following parameters:
--topology_file - topology.yml file to which the script will write the topology information
--connectivity_file - connectivity.json file where you described the fabric connectivity

If no --topology_file specified, the script tries to load topology.yml from the current working directory.
If no --connectivity_file specified, the script tries to load connectivity.json from the current working directory.
"""
    print help
    exit()

show_topology = 0
write_topology = 0

topology_file = ""
connectivity_file = ""

for i in range(0,len(sys.argv)):
    try:
        sys.argv[i].split("=")[1]
    except:
        # do nothing
        arg = ""
        value = ""
    else:
        arg = sys.argv[i].split("=")[0]
        value = sys.argv[i].split("=")[1]
    if arg == "--topology":
        show_topology = 1
    if sys.argv[i] == "--write":
        write_topology = 1
    if arg == "--topology_file":
       topology_file = value
    if arg == "--connectivity_file":
       connectivity_file = value
# --topology_file is generated from --connectivity_file
# if no --topology_file specified and topology.yml exists in the current working directory => stop, error
# same for --connectivity_file

if len(topology_file) == 0:
    try:
        open(wdir+"/topology.yml", "r")
    except:
        print "--topology_file not specified and no topology.yml found in the current working directory"
        exit()
    else:
        topology_file = wdir+"/topology.yml"

if len(connectivity_file) == 0:
    try:
        open(wdir+"/connectivity.json", "r")
    except:
        print "--connectivity_file not specified and no connectivity.json found in the current working directory"
        exit()
    else:
        connectivity_file = wdir+"/connectivity.json"

if len(topology_file) == 0 or len(connectivity_file) == 0:
    print "--topology_file and --connectivity_file must be specified."     
    exit()

try:
    dir = os.path.dirname(topology_file)
except Exception as e:
    print "Check --topology_file {}".format(str(e))
    exit()

try:
    open(topology_file, "a")
except Exception as e:
    print "Check --topology_file {}".format(str(e))
    exit()

try:
    open(connectivity_file, "r")
except Exception as e:
    print "Check --connectivity_file {}".format(str(e))
    exit()

#connectivity="/tftpboot/scripts/tshoot/check_cabling/connectivity.json"
#topology_file="/root/ansible/fabric/topology.yml"

groups = ("spine","leaf","bleaf","bgw")
# wan routers have in the name
look = "wan"

connectivity = connectivity_file

with open(connectivity, 'r') as connectivity_file:
    conn_db = connectivity_file.read()
conn_obj = json.loads(conn_db)
conn_db_nodes = dict()
for i in groups:
    conn_db_nodes[i] = list()
nes = conn_obj["ne"]
# print(nes)
# [{u'connectivity': [{u'local_ifx': u'mgmt0', u'remote_ne': u'SW-CORP.priv.gsp-france-lab.com', u'remote_ifx': u'Eth103/1/5'}, {u'local_ifx': u'Eth1/31', u'remote_ne': u'n9k-leaf-5', u'remote_ifx': u'Ethernet1/49'}, {u'local_ifx': u'Eth1/32', u'remote_ne': u'n9k-bleaf-3', u'remote_ifx': u'Ethernet1/49'}, {u'local_ifx': u'Eth1/33', u'remote_ne': u'n9k-bgw-3', u'remote_ifx': u'Ethernet1/49'}, {u'local_ifx': u'Eth1/34', u'remote_ne': u'n9k-bgw-4', u'remote_ifx': u'Ethernet1/49'}], u'name': u'n9k-spine-2'}, {u'connectivity': [{u'local_ifx': u'mgmt0', u'remote_ne': u'SW-CORP.priv.gsp-france-lab.com', u'remote_ifx': u'Eth103/1/6'}, {u'local_ifx': u'Eth1/49', u'remote_ne': u'n9k-spine-2', u'remote_ifx': u'Ethernet1/31'}], u'name': u'n9k-leaf-5'}, {u'connectivity': [{u'local_ifx': u'mgmt0', u'remote_ne': u'SW-CORP.priv.gsp-france-lab.com', u'remote_ifx': u'Eth103/1/7'}, {u'local_ifx': u'Eth1/49', u'remote_ne': u'n9k-spine-2', u'remote_ifx': u'Ethernet1/32'}], u'name': u'n9k-bleaf-3'}, {u'connectivity': [{u'local_ifx': u'mgmt0', u'remote_ne': u'SW-CORP.priv.gsp-france-lab.com', u'remote_ifx': u'Eth103/1/9'}, {u'local_ifx': u'Eth1/49', u'remote_ne': u'n9k-spine-2', u'remote_ifx': u'Ethernet1/33'}, {u'local_ifx': u'Eth1/20', u'remote_ne': u'wan', u'remote_ifx': u'Ethernet1/4'}], u'name': u'n9k-bgw-3'}, {u'connectivity': [{u'local_ifx': u'mgmt0', u'remote_ne': u'SW-CORP.priv.gsp-france-lab.com', u'remote_ifx': u'Eth103/1/8'}, {u'local_ifx': u'Eth1/49', u'remote_ne': u'n9k-spine-2', u'remote_ifx': u'Ethernet1/34'}, {u'local_ifx': u'Eth1/20', u'remote_ne': u'wan', u'remote_ifx': u'Ethernet1/3'}], u'name': u'n9k-bgw-4'}]

for i in range(0, len(nes)):
    ne_name = conn_obj["ne"][i]["name"]
    for type in groups:
       if re.match('.*-%s-.*' %type,ne_name,re.IGNORECASE):
           if ne_name not in conn_db_nodes[type]: 
	       conn_db_nodes[type].append(ne_name)
'''
conn_db_nodes
{'spine': [u'n9k-spine-1'], 'bleaf': [u'n9k-bleaf-1'], 'leaf': [u'n9k-leaf-1', u'n9k-leaf-2', u'n9k-leaf-3', u'n9k-leaf-4']}
'''

'''
build json inventory that ansible expects
'''
data = {}
data["_meta"] = dict()

for type in groups:
    if type not in data:    
        data[type]=dict()
	data[type]["hosts"] = list()
        data[type]["vars"] = dict()
    for node in conn_db_nodes[type]:
        data[type]["hosts"].append(node)

# this is needed when the script is called from ansible-playbook -i inventory.py
print json.dumps(data,indent=4)

'''
build the topology file
'''
topology=dict()
topology["topology"]=dict()

nodes=dict()
nodes["nodes"]=dict()
count = 0
for type in conn_db_nodes:
  for name in conn_db_nodes[type]:
    nodes["nodes"][count] = name
    count += 1

for i in conn_db_nodes:
    for j in conn_db_nodes[i]:
        topology["topology"][j]=dict()
  
topo = topology["topology"]

for i in range(0, len(nes)):
    ne_name = conn_obj["ne"][i]["name"]
    ne_connectivity = conn_obj["ne"][i]["connectivity"]
    if ne_name in topo:
        n = 0
        if ne_name in conn_db_nodes["leaf"] or ne_name in conn_db_nodes["bleaf"] or ne_name in conn_db_nodes["bgw"]:
            for j in conn_db_nodes["spine"]:
                for k in range(0, len(ne_connectivity)):
                    if ne_connectivity[k]["remote_ne"] == j:
                        topo[ne_name][n]=dict()
                        topo[ne_name][n]["local_ifx"]=ne_connectivity[k]["local_ifx"]
                        topo[ne_name][n]["remote_ifx"]=ne_connectivity[k]["remote_ifx"]
                        topo[ne_name][n]["linkid"]=""
			topo[ne_name][n]["portid"]=""
                        topo[ne_name][n]["peer"]=ne_connectivity[k]["remote_ne"]
                        topo[ne_name][n]["linktype"]="fabric"
                        n+=1
        if ne_name in conn_db_nodes["spine"]:
            for j in conn_db_nodes["leaf"]:
                for k in range(0, len(ne_connectivity)):
                    if ne_connectivity[k]["remote_ne"] == j:
                        topo[ne_name][n]=dict()
                        topo[ne_name][n]["local_ifx"]=ne_connectivity[k]["local_ifx"]
                        topo[ne_name][n]["remote_ifx"]=ne_connectivity[k]["remote_ifx"]
                        topo[ne_name][n]["linkid"]=""
			topo[ne_name][n]["portid"]=""
                        topo[ne_name][n]["peer"]=ne_connectivity[k]["remote_ne"]
                        n+=1
            for j in conn_db_nodes["bleaf"]: 
                for k in range(0, len(ne_connectivity)):
                    if ne_connectivity[k]["remote_ne"] == j:
                        topo[ne_name][n]=dict()
                        topo[ne_name][n]["local_ifx"]=ne_connectivity[k]["local_ifx"]
                        topo[ne_name][n]["remote_ifx"]=ne_connectivity[k]["remote_ifx"]
                        topo[ne_name][n]["linkid"]=""
			topo[ne_name][n]["portid"]=""
                        topo[ne_name][n]["peer"]=ne_connectivity[k]["remote_ne"]
                        n+=1
            for j in conn_db_nodes["bgw"]:
                for k in range(0, len(ne_connectivity)):
                    if ne_connectivity[k]["remote_ne"] == j:
                        topo[ne_name][n]=dict()
                        topo[ne_name][n]["local_ifx"]=ne_connectivity[k]["local_ifx"]
                        topo[ne_name][n]["remote_ifx"]=ne_connectivity[k]["remote_ifx"]
                        topo[ne_name][n]["linkid"]=""
                        topo[ne_name][n]["portid"]=""
                        topo[ne_name][n]["peer"]=ne_connectivity[k]["remote_ne"]
                        n+=1
# topo dict
# {u'n9k-bgw-3': {0: {'peer': u'n9k-spine-2', 'linkid': '', 'local_ifx': u'Eth1/49', 'portid': '', 'remote_ifx': u'Ethernet1/33'}}, u'n9k-bgw-4': {0: {'peer': u'n9k-spine-2', 'linkid': '', 'local_ifx': u'Eth1/49', 'portid': '', 'remote_ifx': u'Ethernet1/34'}}, u'n9k-leaf-5': {0: {'peer': u'n9k-spine-2', 'linkid': '', 'local_ifx': u'Eth1/49', 'portid': '', 'remote_ifx': u'Ethernet1/31'}}, u'n9k-bleaf-3': {0: {'peer': u'n9k-spine-2', 'linkid': '', 'local_ifx': u'Eth1/49', 'portid': '', 'remote_ifx': u'Ethernet1/32'}}, u'n9k-spine-2': {0: {'peer': u'n9k-leaf-5', 'linkid': '', 'local_ifx': u'Eth1/31', 'portid': '', 'remote_ifx': u'Ethernet1/49'}, 1: {'peer': u'n9k-bleaf-3', 'linkid': '', 'local_ifx': u'Eth1/32', 'portid': '', 'remote_ifx': u'Ethernet1/49'}, 2: {'peer': u'n9k-bgw-3', 'linkid': '', 'local_ifx': u'Eth1/33', 'portid': '', 'remote_ifx': u'Ethernet1/49'}, 3: {'peer': u'n9k-bgw-4', 'linkid': '', 'local_ifx': u'Eth1/34', 'portid': '', 'remote_ifx': u'Ethernet1/49'}}}

'''
read topology and determine fabric and dci links for the bgw, update topo
'''
bgw = dict()
bgw["tracking"] = dict()
bgw["tracking"]["fabric"] = dict()

bgw["tracking"]["dci"] = dict()

for bgw_node in topo:
    if re.match('.*-bgw-.*',bgw_node,re.IGNORECASE):
        topo_bgw = topo[bgw_node]
        #print(topo_bgw)
        bgw["tracking"]["fabric"][bgw_node] = dict()
        bgw["tracking"]["dci"][bgw_node] = dict()

        for i in range(0, len(nes)):
            ne_name = conn_obj["ne"][i]["name"]
            ne_connectivity = conn_obj["ne"][i]["connectivity"]
            if ne_name == bgw_node:
                n = 0
                for k in range(0, len(ne_connectivity)):
                    remote_ne = ne_connectivity[k]["remote_ne"]
                    if re.match('.*'+look+'.*',remote_ne,re.IGNORECASE):
                        bgw["tracking"]["dci"][bgw_node][n] = dict()
                        bgw["tracking"]["dci"][bgw_node][n]["local_ifx"] = ne_connectivity[k]["local_ifx"]
                        bgw["tracking"]["dci"][bgw_node][n]["remote_ifx"] = ne_connectivity[k]["remote_ifx"]
                        bgw["tracking"]["dci"][bgw_node][n]["peer"] = remote_ne
                        n+=1
                    else:
                        if remote_ne in topo:
                            bgw["tracking"]["fabric"][bgw_node][n] = dict()
                            bgw["tracking"]["fabric"][bgw_node][n]["local_ifx"] = ne_connectivity[k]["local_ifx"]
                            bgw["tracking"]["fabric"][bgw_node][n]["remote_ifx"] = ne_connectivity[k]["remote_ifx"]
                            bgw["tracking"]["fabric"][bgw_node][n]["peer"] = remote_ne
                            n+=1

''' 
read topology and determine linkid and portid
start from spine / spines
'''
nbr_spine = 0
nbr_leaf = 0

for node_type in groups:
    for i in conn_db_nodes[node_type]:
        if node_type=="spine":
            nbr_spine += 1
        if re.match("(.*)leaf",node_type, re.IGNORECASE):
        #if node_type=="leaf" or node_type=="bleaf":
            nbr_leaf += 1

linkid_iter = 0

for spine in conn_db_nodes["spine"]:
    topo_spine = topo[spine]
    for i in range(0, len(topo_spine)):
        s_ifx = topo_spine[i]["local_ifx"]
        l_ifx = topo_spine[i]["remote_ifx"]
        leaf = topo_spine[i]["peer"]
	if leaf in topo:
            topo_leaf = topo[leaf]
            for j in range(0, len(topo_leaf)):
	        if topo_leaf[j]["peer"] == spine:
                    if re.split("([a-zA-Z]{3,})",topo_leaf[j]["remote_ifx"], re.IGNORECASE)[2] == re.split("([a-zA-Z]{3,})",s_ifx, re.IGNORECASE)[2]:
                        if re.split("([a-zA-Z]{3,})",topo_leaf[j]["local_ifx"], re.IGNORECASE)[2] == re.split("([a-zA-Z]{3,})",l_ifx, re.IGNORECASE)[2]:
			    topo_spine[i]["linkid"]=linkid_iter
                            topo_spine[i]["portid"]=0 
		            topo_leaf[j]["linkid"]=linkid_iter 
                            topo_leaf[j]["portid"]=1
                            linkid_iter += 1
'''
determine vpc pair
'''
vpc_pairs = dict()
vpc_pairs["vpc_pairs"] = dict()

vpcpairs = vpc_pairs["vpc_pairs"]

nes = conn_obj["ne"]
#conn_db_nodes
vpc_candidates = list()

for node_type in conn_db_nodes:
    if re.match("(.*)leaf",node_type, re.IGNORECASE):
        for i in range(0, len(conn_db_nodes[node_type])):
            vpc_candidates.append(conn_db_nodes[node_type][i])

vpc_pair_count = 0
vpc_candidate_seen = list()

for i in range(0, len(nes)):
    ne_name = conn_obj["ne"][i]["name"]     
    if ne_name in vpc_candidates:
        ne_connectivity = conn_obj["ne"][i]["connectivity"]
        for k in range(0, len(ne_connectivity)):
            if ne_connectivity[k]["remote_ne"].lower() in vpc_candidates:
                vpc_candidate_seen.append(ne_connectivity[k]["remote_ne"].lower())
                if ne_name not in vpc_candidate_seen:
                    vpcpairs[vpc_pair_count] = (ne_name, ne_connectivity[k]["remote_ne"])
                    vpc_candidate_seen.append(ne_name.lower())                
                    vpc_pair_count += 1

'''
determine vpc interfaces
'''

vpc_interfaces = dict()
vpc_interfaces["vpc_interfaces"] = dict()
vpcinterfaces = vpc_interfaces["vpc_interfaces"]

nes = conn_obj["ne"]

for id, vpcnodes in vpcpairs.iteritems():
    for ivpcnodes in vpcnodes:
      vpcinterfaces[ivpcnodes] = list()
      for i in range(0, len(nes)):
        ne_name = conn_obj["ne"][i]["name"]
        if ne_name == ivpcnodes:
          ne_connectivity = conn_obj["ne"][i]["connectivity"]
          for k in range(0, len(ne_connectivity)):
            if ne_connectivity[k]["remote_ne"] in vpcnodes:
              vpcinterfaces[ivpcnodes].append(ne_connectivity[k]["local_ifx"]) 

if write_topology == 1:

    try:
        with open(topology_file, 'w') as yaml_file:
            yaml.safe_dump(nodes, yaml_file, default_flow_style=False)
            yaml.safe_dump(vpc_pairs, yaml_file, default_flow_style=False)
            yaml.safe_dump(vpc_interfaces, yaml_file, default_flow_style=False)
            yaml.safe_dump(bgw, yaml_file, default_flow_style=False)
            yaml.safe_dump(topology, yaml_file, default_flow_style=False)
    except:
        print ""
        print ("Not possible to write the topology information to %s" % topology_file)
    else:
        print ""
        print ("The topology information was written to the topology file %s" % topology_file)

if show_topology ==1:
    print ""
    print yaml.safe_dump(nodes, default_flow_style=False)  
    print yaml.safe_dump(vpc_pairs, default_flow_style=False)
    print yaml.safe_dump(vpc_interfaces, default_flow_style=False)
    print yaml.safe_dump(bgw, default_flow_style=False)
    print yaml.safe_dump(topology, default_flow_style=False)
