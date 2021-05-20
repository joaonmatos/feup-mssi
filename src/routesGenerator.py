import xml.etree.ElementTree as ET
import subprocess
import randomTrips


class RoutesGenerator:

    def __init__(self, original_net_xml_filename, tlp_net_xml_filename):
        self.original_net_xml_filename = original_net_xml_filename
        self.tlp_net_xml_filename = tlp_net_xml_filename

    def generate_trips(self):
        #randomTrips.main(randomTrips.get_options(["-n " + self.original_net_xml_filename,"-e 50", "--vehicle-class UAMS", "--trip-attributes=\"maxSpeed=\\\"27.8\\\""]))
        randomTrips.main(randomTrips.get_options(
            ["-n", self.original_net_xml_filename, "-e", "10000", "-p", "20", "-o", "output/trips.trips.xml"]))
        # subprocess.run(["randomTrips.py", "--sumo-net-file",  filename ,"--plain-output-prefix"])

    def generate_route_files(self):
        subprocess.run(["duarouter", "-n", self.original_net_xml_filename, "--route-files",
                       "output/trips.trips.xml", "-o", "output/original.rou.xml", "--repair", "true", "--ignore-errors"])
        subprocess.run(["duarouter", "-n", self.tlp_net_xml_filename, "--route-files",
                       "output/trips_UAMS.trips.xml", "-o", "output/tlp.rou.xml", "--repair", "true", "--ignore-errors"])

    # Might be usefull
    def generate_configVehTypeDistribution(self, filename):
        f = open("output/" + filename, "w+")

        f.write("vClass; costume1")
        f.close("carFollowModel; Krauss")

    def add_UAMS(self):
        #Open trips
        self.trips_xml_tree = ET.parse("output/trips.trips.xml")
        self.trips_xml_root = self.trips_xml_tree.getroot()
        
        
        #<vType id="custom1" vClass="custom1"/>
        trips_routes_node = ET.Element('vType')
        trips_routes_node.set("id", "costume1")
        trips_routes_node.set("vClass", "bus")
        self.trips_xml_root.insert(0, trips_routes_node)

        #Adding x ratio of costume1 trips
        x = 0.1

        trips = self.trips_xml_root.findall("trip")
        for i in range(int(round(len(trips)*x))):
            trips[i].set("type", "costume1")
 
        #Save Trips
        self.trips_xml_tree.write("output/trips_UAMS.trips.xml")
        
        pass

    def create_UAMS_vType(self, filename):
        f = open("output/" + filename, "w+")
        f.write("<additional>")
        f.write("  <vType id=\"myType\" maxSpeed=\"27\" vClass=\"passenger\"/>")
        f.write("</additional>")

        f.write("<additional>")
        f.close("<vType id=\"myType\" maxSpeed=\"27\" vClass=\"passenger\"/>")


generator = RoutesGenerator("input/feup.net.xml", "output/net.net.xml")
generator.generate_trips()
generator.add_UAMS()
generator.generate_route_files()
