import xml.etree.ElementTree as ET
import subprocess
import math
import itertools

class TlpMutator():

    def getPlainXML(self, filename):
        subprocess.run(["netconvert", "--sumo-net-file",  filename ,"--plain-output-prefix"])    
    
    def storePlainXML(self):
        subprocess.run(["netconvert", "--node-files=true.nod.xml", "--edge-files=true.edg.xml",
         "--connection-files=true.con.xml","--tllogic-files=true.tll.xml", "--type-files=true.typ.xml"])    

    def __init__(self, net_xml_filename):
        
        #Separate net.xml
        self.getPlainXML(net_xml_filename)
        
        #Open edges
        self.edg_xml_tree = ET.parse("true.edg.xml")
        self.edg_xml_root = self.edg_xml_tree.getroot()

        #Open nodes
        self.node_xml_tree = ET.parse("true.nod.xml")
        self.node_xml_root = self.node_xml_tree.getroot()
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
            self.parsed_nodes[node.get("id")] = {"x" : node.get("x"), "y" : node.get("y")}

        #usefull list of added nodes
        self.added_nodes = []


    def get_closest_node(self, x, y):
        distance = None
        closest_ñode = None
        for node in self.parsed_nodes:
            node_x = self.parsed_nodes.get(node).get('x')
            node_y = self.parsed_nodes.get(node).get('y')
            x_pitagoras = pow(x - float(node_x), 2)
            y_pitagoras = pow(y - float(node_y), 2)
            node_distance = math.sqrt(x_pitagoras + y_pitagoras)
            if distance is None or distance > node_distance:
                closest_node = node
                distance = node_distance
        return closest_node

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
                subelement = ET.SubElement(self.node_xml_root, 'node')
                subelement.set("id", node_name)
                subelement.set("x", str(x_offset + self.min_x))
                subelement.set("y", str(y_offset + self.min_y))
                subelement.set("type", "priority")
                
                self.added_nodes.append(node_name)

                #Add edge

                closest_node = self.get_closest_node(x_offset + self.min_x, y_offset + self.min_y)
                subelement = ET.SubElement(self.edg_xml_root, 'edge')
                subelement.set("id", "TLP_to_net_edge_" + str(i) + "_" + str(j))
                subelement.set("from", node_name)
                subelement.set("to", closest_node)
                subelement.set("priority", "1")
                subelement.set("numLanes", "1")
                subelement.set("speed", "13.89")
                subelement.set("allow", "custom1")
                
                
        #Adding flight edges
        self.add_flight_edges()

        #Write nodes
        self.node_xml_tree.write("true.nod.xml")
        
        #Write nedges
        self.edg_xml_tree.write("true.edg.xml")


    def add_flight_edges(self):
        for pair in itertools.combinations(self.added_nodes, 2):
            print("adding flight edg " + pair[0] + " " + pair[1])
            subelement = ET.SubElement(self.edg_xml_root, 'edge')
            subelement.set("id", "TLP_to_TLP_edge_" + str(pair[0]) + "_" + str(pair[1]))
            subelement.set("from", pair[0])
            subelement.set("to", pair[1])
            subelement.set("priority", "1")
            subelement.set("numLanes", "1")
            subelement.set("speed", "13.89")
            subelement.set("allow", "custom1")

        

tlp_mutator = TlpMutator("feup.net.xml")
tlp_mutator.generate_mutated_XML(4)
tlp_mutator.storePlainXML()