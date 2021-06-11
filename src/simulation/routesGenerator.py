from random import random
import xml.etree.ElementTree as ET
import subprocess
import randomTrips


class RoutesGenerator:

    def __init__(self, original_net_xml_filename, tlp_net_xml_filename):
        self.original_net_xml_filename = original_net_xml_filename
        self.tlp_net_xml_filename = tlp_net_xml_filename

    def generate_trips(self, trips_xml_filename, simulation_time, trips):
        #randomTrips.main(randomTrips.get_options(["-n " + self.original_net_xml_filename,"-e 50", "--vehicle-class UAMS", "--trip-attributes=\"maxSpeed=\\\"27.8\\\""]))
        randomTrips.main(randomTrips.get_options(
            ["-n", self.original_net_xml_filename, "-e", simulation_time, "-p", str(simulation_time/trips), "-o", trips_xml_filename]))
        # subprocess.run(["randomTrips.py", "--sumo-net-file",  filename ,"--plain-output-prefix"])

    def generate_route_files(self, trips_xml_filename, routes_xml_filename):
        subprocess.run(["duarouter", "-n", self.tlp_net_xml_filename, "--route-files",
                       trips_xml_filename,
                       "--ignore-errors", "-o", routes_xml_filename, "-W"])

    def add_UAMS(self, ratio, trips_xml_filename, new_trips_xml_filename):
        # Open trips
        self.trips_xml_tree = ET.parse(trips_xml_filename)
        self.trips_xml_root = self.trips_xml_tree.getroot()

        # <vType id="custom1" vClass="custom1"/>
        vType_node = ET.Element('vType')
        vType_node.set("id", "UAMS")
        vType_node.set("vClass", "custom1")
        vType_node.set("maxSpeed", "75")
        vType_node.set("color", "1,0,1")

        self.trips_xml_root.insert(0, vType_node)

        # Adding x ratio of custom1 trips
        x = ratio

        trips = self.trips_xml_root.findall("trip")
        for i in range(len(trips)):
            if random() < x:
                trips[i].set("type", "UAMS")

        # Save Trips
        self.trips_xml_tree.write(new_trips_xml_filename)

        pass


# generator = RoutesGenerator("input/mts.net.xml", "output/net.net.xml")
# generator.generate_trips()
# generator.add_UAMS()
# generator.generate_route_files()
