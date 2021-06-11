from __future__ import with_statement
import xml.etree.ElementTree as ET
import subprocess
import math
import itertools
import os
import time

DEBUG = True

class TlpMutator():
    
    added_edges = {}

    def __init__(self):
    	pass

    #--geometry.remove --ramps.guess --junctions.join --tls.guess-signals --tls.discard-simple --tls.join --tls.default-type actuated
    def importOSM(self, filename, output_file):
        subprocess.run(["netconvert", "--osm", filename ,"-o", output_file, "--geometry.remove", "--ramps.guess", "--junctions.join", "--tls.guess-signals", "--tls.discard-simple", "--tls.join", "--tls.default-type", "actuated", "--keep-edges.by-vclass", "custom1", "--remove-edges.isolated" ])
    
    def getPlainXML(self, filename):
        subprocess.run(["netconvert", "--sumo-net-file", filename ,"--plain-output-prefix", "true"])
    
    def storePlainXML(self, mutated_net_filename):
        subprocess.run(["netconvert", "--node-files=true.nod.xml", "--edge-files=true.edg.xml",
         "--connection-files=true.con.xml","--tllogic-files=true.tll.xml", "--type-files=true.typ.xml",
         "--plain.extend-edge-shape", "--junctions.join", "-o", mutated_net_filename, "-v"])
        self.added_edges = {}  
    
    def cleanup(self):
        os.remove("true.con.xml")
        os.remove("true.edg.xml")
        os.remove("true.nod.xml")
        os.remove("true.tll.xml")
        os.remove("true.typ.xml")
    
    def deconstruct_net_file(self, net_xml_filename):
        
        #Separate net.xml
        self.getPlainXML(net_xml_filename)
        
        #Open edges
        self.edg_xml_tree = ET.parse("true.edg.xml")
        self.edg_xml_root = self.edg_xml_tree.getroot()
        
        #Open nodes
        self.node_xml_tree = ET.parse("true.nod.xml")
        self.node_xml_root = self.node_xml_tree.getroot()

        #Open connections
        self.con_xml_tree = ET.parse("true.con.xml")
        self.con_xml_root = self.con_xml_tree.getroot()

        #Get map size
        boundary = self.node_xml_root.find("location").get("convBoundary")
        min_x_str, min_y_str, max_x_str, max_y_str = boundary.split(",")
        self.min_x = float(min_x_str)
        self.max_x = float(max_x_str)
        self.min_y = float(min_y_str)
        self.max_y = float(max_y_str)

        #getting all nodes for TLP connection
        nodes = self.node_xml_root.findall("node")
        self.parsed_nodes = {}
        for node in nodes:
            self.parsed_nodes[node.get("id")] = {"id" : node.get("id"), "x" : node.get("x"), "y" : node.get("y")}

        #usefull list of added nodes
        self.added_nodes = []


    def get_closest_node(self, x, y):
        distance = None
        closest_node = None
        inbound_edge = None
        outbound_edge = None
        for node in self.parsed_nodes:
            node_x = self.parsed_nodes.get(node).get('x')
            node_y = self.parsed_nodes.get(node).get('y')
            x_pitagoras = pow(x - float(node_x), 2)
            y_pitagoras = pow(y - float(node_y), 2)
            node_distance = math.sqrt(x_pitagoras + y_pitagoras)
            if distance is None or distance > node_distance:
                is_reachable, inbound, outbound = self.is_reachable_by_car(self.parsed_nodes.get(node))
                print("IS REACHABLE: " + str(is_reachable) + str(inbound_edge) + str(outbound_edge))
                if is_reachable:
                    closest_node = node
                    distance = node_distance
                    inbound_edge = inbound
                    outbound_edge = outbound 
        return closest_node, inbound_edge, outbound_edge

    def is_reachable_by_car(self, node):
        inboud = None
        outbound = None
        for edge in self.edg_xml_root.findall("edge"):
            if edge.get('to') == node.get('id'):
                if edge.get("disallow"):
                    if "passenger" not in edge.get("disallow"):
                        log("DISALLOW " + edge.get("id") + " " + edge.get("disallow"))
                        inboud = edge.get('id')
                if edge.get("allow"):   
                    if "passenger" in edge.get("allow"):
                        log("ALLOW " + edge.get("id") + " " + edge.get("allow"))
                        inboud = edge.get('id')
            if edge.get('from') == node.get('id'):
                if edge.get("disallow"):
                    if "passenger" not in edge.get("disallow"):
                        log("DISALLOW " + edge.get("id") + " " + edge.get("disallow"))
                        outbound = edge.get('id')
                if edge.get("allow"):   
                    if "passenger" in edge.get("allow"):
                        log("ALLOW " + edge.get("id") + " " + edge.get("allow"))
                        outbound = edge.get('id')
            if outbound is not None and inboud is not None:
                return True, inboud, outbound
        return False, None, None

    #added_edges = {<edge_name>: edge_len}
    def generate_weight_file(self):

        # <meandata>
        #     <interval begin="0" end="3600" id="whatever">
        #         <edge id="edgeID1" traveltime="23"/>
        #         <edge id="edgeID2" traveltime="1000"/>
        #     </interval>
        # </meandata>

        root = ET.Element("meandata")
        interval = ET.SubElement(root, "interval")
        interval.set("begin", "0")
        interval.set("end", "10000")
        interval.set("id", "flight_edges")
        
        for id in self.added_edges:
            print( "id: " + str(id) + "len: " + str(self.added_edges[id]))
            edge = ET.SubElement(interval, "edge")
            edge.set("id", id)
            edge.set("traveltime", str(self.added_edges[id]))
        tree = ET.ElementTree(root)
        tree.write("output/custom.weights.xml")
        return

    #Density in n_of_TLPs/km^2
    def generate_mutated_XML(self, density):

        # <junction id="leftBottom" type="priority" x="0.00" y="50.00" incLanes="leftTop_to_leftBottom_0 middleBottom_to_leftBottom_0" intLanes=":leftBottom_0_0 :leftBottom_1_0" shape="-3.20,53.20 3.20,53.20 3.20,46.80">
        #     <request index="0" response="00" foes="00" cont="0"/>
        #     <request index="1" response="00" foes="00" cont="0"/>
        # </junction>


        x_size = self.max_x - self.min_x
        y_size = self.max_y - self.min_y
        

        
        for i in range(density):
            x_grid_cell_len = x_size/density
            x_offset = i * x_grid_cell_len + x_grid_cell_len/2
            
            for j in range(density):
                y_grid_cell_len = y_size/density
                y_offset = j * y_grid_cell_len + y_grid_cell_len/2
                
                #Add node
               
                node_name = "TLP_" + str(i) + "_" + str(j)
                xml_elem_node = ET.SubElement(self.node_xml_root, 'node')
                xml_elem_node.set("id", node_name)
                xml_elem_node.set("x", str(x_offset + self.min_x))
                xml_elem_node.set("y", str(y_offset + self.min_y))
                xml_elem_node.set("type", "priority")
                
                self.added_nodes.append({"id" : node_name, "x" : xml_elem_node.get("x"), "y" : xml_elem_node.get("y")})

                #Add edge

                closest_node, inbound_edge, outbound_edge  = self.get_closest_node(x_offset + self.min_x, y_offset + self.min_y)

                
                xml_elem_edge = ET.SubElement(self.edg_xml_root, 'edge')

                id_from = "TLP_to_net_edge_" + str(i) + "_" + str(j) + "_from"
                xml_elem_edge.set("id", id_from)
                xml_elem_edge.set("from", node_name)
                xml_elem_edge.set("to", closest_node)
                xml_elem_edge.set("priority", "1")
                xml_elem_edge.set("numLanes", "1")
                xml_elem_edge.set("speed", "13.89")
                xml_elem_edge.set("allow", "custom1")
                
                xml_elem_edge = ET.SubElement(self.edg_xml_root, 'edge')

                id_to = "TLP_to_net_edge_" + str(i) + "_" + str(j) + "_to"    
                xml_elem_edge.set("id", id_to)
                xml_elem_edge.set("from", closest_node)
                xml_elem_edge.set("to", node_name)
                xml_elem_edge.set("priority", "1")
                xml_elem_edge.set("numLanes", "1")
                xml_elem_edge.set("speed", "13.89")
                xml_elem_edge.set("allow", "custom1")

                #Add connection

                xml_elem_con_1 = ET.SubElement(self.con_xml_root, 'connection')
                xml_elem_con_1.set("from", str(inbound_edge))
                xml_elem_con_1.set("to", str(id_to))
                xml_elem_con_1.set("fromLane", "0") 
                xml_elem_con_1.set("toLane", "0") 

                xml_elem_con_2 = ET.SubElement(self.con_xml_root, 'connection')
                xml_elem_con_2.set("from", str(id_from))
                xml_elem_con_2.set("to", str(outbound_edge))
                xml_elem_con_2.set("fromLane", "0") 
                xml_elem_con_2.set("toLane", "0") 

        #[Deprecated]
        # #Disjoining nodes
        # #<joinExclude nodes=""/>
        # xml_elem_joinExculde = ET.SubElement(self.node_xml_root, 'joinExclude')
        # separator = " "
        # xml_elem_joinExculde.set("nodes", separator.join(self.added_nodes))                
                
        #Adding flight edges
        self.add_flight_edges()

        #Write nodes
        self.node_xml_tree.write("./true.nod.xml", encoding="utf-8", xml_declaration=True)
        
        #Write edges
        print(self.edg_xml_tree)
        self.edg_xml_tree.write("./true.edg.xml", encoding="utf-8", xml_declaration=True)

        #Write connections        
        print(self.con_xml_tree)
        self.con_xml_tree.write("true.con.xml")


    def add_flight_edges(self):
        for pair in itertools.combinations(self.added_nodes, 2):
            node0_id = pair[0].get('id')
            node1_id = pair[1].get('id')
            log("adding flight edg " + node0_id + " " + node1_id)
            
            id = "TLP_to_TLP_edge_" + str(node0_id) + "_" + str(node1_id)
            xml_elem_edge = ET.SubElement(self.edg_xml_root, 'edge')
            xml_elem_edge.set("id", id)
            #xml_elem_edge.set("type", "airlane")
            xml_elem_edge.set("from", node0_id)
            xml_elem_edge.set("to", node1_id)
            xml_elem_edge.set("priority", "2")
            xml_elem_edge.set("numLanes", "1")
            xml_elem_edge.set("speed", "75.00")
            xml_elem_edge.set("allow", "custom1") # is custom 1 the best option or de we create a vehicle type?
            
            #shape calculation
            node0_x = float(pair[0].get('x'))
            node1_x = float(pair[1].get('x'))
            node0_y = float(pair[0].get('y'))
            node1_y = float(pair[1].get('y'))

            half_x = (node0_x + node1_x)/2
            half_y = (node0_y + node1_y)/2

            height = (math.atan2(node1_x-node0_x, node1_y-node0_y)/math.pi) * 25 + 200
            shape_str = str(half_x) + "," + str(half_y) + "," + str(height)
            log(shape_str)
            xml_elem_edge.set("shape",shape_str)

            self.added_edges[id] = 1

            #Second edge
            log("adding flight edg " + node1_id + " " + node0_id)
            
            id = "TLP_to_TLP_edge_" + str(node1_id) + "_" + str(node0_id)
            xml_elem_edge_2 = ET.SubElement(self.edg_xml_root, 'edge')
            xml_elem_edge_2.set("id", id)
            #xml_elem_edge.set("type", "airlane")
            xml_elem_edge_2.set("from", node1_id)
            xml_elem_edge_2.set("to", node0_id)
            xml_elem_edge_2.set("priority", "2")
            xml_elem_edge_2.set("numLanes", "1")
            xml_elem_edge_2.set("speed", "75.00")
            xml_elem_edge_2.set("allow", "custom1") # is custom 1 the best option or de we create a vehicle type?
            
            #shape calculation
            node0_x = float(pair[0].get('x'))
            node1_x = float(pair[1].get('x'))
            node0_y = float(pair[0].get('y'))
            node1_y = float(pair[1].get('y'))

            half_x = (node0_x + node1_x)/2
            half_y = (node0_y + node1_y)/2

            height = (math.atan2(node0_x-node1_x, node0_y-node1_y)/math.pi) * 25 + 200
            shape_str = str(half_x) + "," + str(half_y) + "," + str(height)
            log(shape_str)
            xml_elem_edge_2.set("shape",shape_str)

            self.added_edges[id] = 1

def log(s):
    if DEBUG:
        print(s)

#tlp_mutator = TlpMutator("input/feup.net.xml")
# tlp_mutator = TlpMutator("input/mts.net.xml")
# tlp_mutator.generate_mutated_XML(3)
# tlp_mutator.storePlainXML()

# #TODO: Add to typ file
# <types>
#     <type id="airlane" priority="13" numLanes="10" speed="160" />
# </types>