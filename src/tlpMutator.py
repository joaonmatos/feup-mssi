import xml.etree.ElementTree as ET
import subprocess
import math
import itertools

DEBUG = True


class TlpMutator():

    def getPlainXML(self, filename):
        subprocess.run(["netconvert", "--sumo-net-file",
                       filename, "--plain-output-prefix"])

    def storePlainXML(self):
        subprocess.run(["netconvert", "--node-files=true.nod.xml", "--edge-files=true.edg.xml",
                        "--connection-files=true.con.xml", "--tllogic-files=true.tll.xml", "--type-files=true.typ.xml", "--plain.extend-edge-shape"])

    def __init__(self, net_xml_filename):

        # Separate net.xml
        self.getPlainXML(net_xml_filename)

        # Open edges
        self.edg_xml_tree = ET.parse("true.edg.xml")
        self.edg_xml_root = self.edg_xml_tree.getroot()

        # [DEPRECATED]
        # #Open type
        # self.typ_xml_tree = ET.parse("true.typ.xml")
        # self.typ_xml_root = self.typ_xml_tree.getroot()

        # Open nodes
        self.node_xml_tree = ET.parse("true.nod.xml")
        self.node_xml_root = self.node_xml_tree.getroot()

        # Get map size
        boundary = self.node_xml_root.find("location").get("convBoundary")
        min_x_str, min_y_str, max_x_str, max_y_str = boundary.split(",")
        self.min_x = float(min_x_str)
        self.max_x = float(max_x_str)
        self.min_y = float(min_y_str)
        self.max_y = float(max_y_str)

        # getting all nodes for TLP connection
        nodes = self.node_xml_root.findall("node")
        self.parsed_nodes = {}
        for node in nodes:
            self.parsed_nodes[node.get("id")] = {"id": node.get(
                "id"), "x": node.get("x"), "y": node.get("y")}

        # usefull list of added nodes
        self.added_nodes = []

    def get_closest_node(self, x, y):
        distance = None
        closest_node = None
        for node in self.parsed_nodes:
            node_x = self.parsed_nodes.get(node).get('x')
            node_y = self.parsed_nodes.get(node).get('y')
            x_pitagoras = pow(x - float(node_x), 2)
            y_pitagoras = pow(y - float(node_y), 2)
            node_distance = math.sqrt(x_pitagoras + y_pitagoras)
            if distance is None or distance > node_distance:
                if self.is_reachable_by_car(self.parsed_nodes.get(node)):
                    closest_node = node
                    distance = node_distance
        return closest_node

    def is_reachable_by_car(self, node):
        for edge in self.edg_xml_root.findall("edge"):
            if edge.get('to') == node.get('id') or edge.get('from') == node.get('id'):
                if edge.get("disallow"):
                    if "passenger" not in edge.get("disallow"):
                        log("DISALLOW " + edge.get("id") +
                            " " + edge.get("disallow"))
                        return True
                if edge.get("allow"):
                    if "passenger" in edge.get("allow"):
                        log("ALLOW " + edge.get("id") + " " + edge.get("allow"))
                        return True
        return False

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

                # Add node

                node_name = "TLP_" + str(i) + "_" + str(j)
                xml_elem_node = ET.SubElement(self.node_xml_root, 'node')
                xml_elem_node.set("id", node_name)
                xml_elem_node.set("x", str(x_offset + self.min_x))
                xml_elem_node.set("y", str(y_offset + self.min_y))
                xml_elem_node.set("type", "priority")
                xml_elem_node.set("keepClear", "false")

                self.added_nodes.append(
                    {"id": node_name, "x": xml_elem_node.get("x"), "y": xml_elem_node.get("y")})

                # Add edge

                closest_node = self.get_closest_node(
                    x_offset + self.min_x, y_offset + self.min_y)
                xml_elem_edge = ET.SubElement(self.edg_xml_root, 'edge')
                xml_elem_edge.set("id", "TLP_to_net_edge_" +
                                  str(i) + "_" + str(j))
                xml_elem_edge.set("from", node_name)
                xml_elem_edge.set("to", closest_node)
                xml_elem_edge.set("priority", "1")
                xml_elem_edge.set("numLanes", "1")
                xml_elem_edge.set("speed", "13.89")
                xml_elem_edge.set("allow", "custom1")

        # [Deprecated]
        # #Disjoining nodes
        # #<joinExclude nodes=""/>
        # xml_elem_joinExculde = ET.SubElement(self.node_xml_root, 'joinExclude')
        # separator = " "
        # xml_elem_joinExculde.set("nodes", separator.join(self.added_nodes))

        # Adding flight edges
        self.add_flight_edges()

        # Write nodes
        self.node_xml_tree.write("true.nod.xml")

        # Write nedges
        self.edg_xml_tree.write("true.edg.xml")

    def add_flight_edges(self):
        for pair in itertools.combinations(self.added_nodes, 2):
            node0 = pair[0]
            node1 = pair[1]
            node0_id = node0.get('id')
            node1_id = node1.get('id')
            log("adding flight edg " + node0_id + " " + node1_id)
            xml_elem_edge = ET.SubElement(self.edg_xml_root, 'edge')
            xml_elem_edge.set("id", "TLP_to_TLP_edge_" +
                              str(node0_id) + "_" + str(node1_id))
            #xml_elem_edge.set("type", "airlane")
            xml_elem_edge.set("from", node0_id)
            xml_elem_edge.set("to", node1_id)
            xml_elem_edge.set("priority", "1")
            xml_elem_edge.set("numLanes", "1")
            xml_elem_edge.set("speed", "1000.89")
            # is custom 1 the best option or de we create a vehicle type?
            xml_elem_edge.set("allow", "custom1")

            # shape calculation
            node0_x = float(node0.get('x'))
            node1_x = float(node1.get('x'))
            node0_y = float(node0.get('y'))
            node1_y = float(node1.get('y'))

            path = parabolic_path((node0_x, node0_y, 0),
                                  (node1_x, node1_y, 0), 8, 300)

            shape_str = " ".join(node_as_str(node) for node in path[1:-1])

            log(shape_str)
            xml_elem_edge.set("shape", shape_str)


def log(s):
    if DEBUG:
        print(s)

# calculates a parabolic path between point X and Y, by offsetting
# a parabola to the line between the points
#
# *x* is the initial point, as a tuple of coordinates (x, y, z)
# *y* the same but for the final point
# steps is the number of steps taken to interpolate, it means that
# linear interpolation is done once every (1 / steps). e.g. for
# steps = 3, points will be calculated for [0, 0.33, 0.66, 1]
# *max_h* is the max parabolic vertical offset
#
# example: path((0,0,0), (0,1,0), 3, 1) gives:
# [(0.0, 0.0, 0.0), (0.0, 0.3333333333333333, 0.888888888888889),
# (0.0, 0.6666666666666666, 0.888888888888889), (0.0, 1.0, 0.0)]


def parabolic_path(x, y, steps, max_h):
    xx, yx, zx = x
    xy, yy, zy = y
    dx, dy, dz = (xy - xx, yy - yx, zy - zx)

    step = 1 / steps
    rs = [i * step for i in range(steps + 1)]

    p = []
    for r in rs:
        xr = xx + r*dx
        yr = yx + r*dy
        zline = zx + r*dz
        # formula for parabola between roots 0,0 and 1,0 with vertex at 0.5,max_h
        zparab = -4 * max_h * r * (r - 1)
        point = (xr, yr, zline + zparab)
        p.append(point)

    return p


def node_as_str(node_as_tuple):
    x, y, z = node_as_tuple
    return f"{x},{y},{z}"


tlp_mutator = TlpMutator("input/feup.net.xml")
tlp_mutator.generate_mutated_XML(4)
tlp_mutator.storePlainXML()

# #TODO: Add to typ file
# <types>
#     <type id="airlane" priority="13" numLanes="10" speed="160" />
# </types>
