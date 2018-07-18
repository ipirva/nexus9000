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

if len(sys.argv) <= 1:
    help = """
Please use one of the following arguments:
--list - inventory list
--topology - show topology details
--write - write topology details on disk
"""
    print help
    exit()

show_topology = 0
write_topology = 0

for i in range(0,len(sys.argv)):
    if sys.argv[i] == "--topology":
        show_topology = 1
    if sys.argv[i] == "--write":
        write_topology = 1

connectivity="/tftpboot/scripts/tshoot/check_cabling/connectivity.json"
topology_file="/root/ansible/fabric/topology.yml"
groups = ("spine","leaf","bleaf")

with open(connectivity, 'r') as connectivity_file:
    conn_db = connectivity_file.read()
conn_obj = json.loads(conn_db)
conn_db_nodes = dict()
for i in groups:
    conn_db_nodes[i] = list()
nes = conn_obj["ne"]
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
        if ne_name in conn_db_nodes["leaf"] or ne_name in conn_db_nodes["bleaf"]:
            for j in conn_db_nodes["spine"]:
                for k in range(0, len(ne_connectivity)):
                    if ne_connectivity[k]["remote_ne"] == j:
                        topo[ne_name][n]=dict()
                        topo[ne_name][n]["local_ifx"]=ne_connectivity[k]["local_ifx"]
                        topo[ne_name][n]["remote_ifx"]=ne_connectivity[k]["remote_ifx"]
                        topo[ne_name][n]["linkid"]=""
			topo[ne_name][n]["portid"]=""
                        topo[ne_name][n]["peer"]=ne_connectivity[k]["remote_ne"]
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
    print yaml.safe_dump(topology, default_flow_style=False)
