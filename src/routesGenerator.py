import subprocess
import randomTrips

class RoutesGenerator:

    def __init__(self, original_net_xml_filename, tlp_net_xml_filename):
        self.original_net_xml_filename = original_net_xml_filename
        self.tlp_net_xml_filename = tlp_net_xml_filename
    
    def generate_trips(self):
        #randomTrips.main(randomTrips.get_options(["-n " + self.original_net_xml_filename,"-e 50", "--vehicle-class UAMS", "--trip-attributes=\"maxSpeed=\\\"27.8\\\""]))
        randomTrips.main(randomTrips.get_options(["-n", self.original_net_xml_filename,"-e", "50"]))
        # subprocess.run(["randomTrips.py", "--sumo-net-file",  filename ,"--plain-output-prefix"])    

    def generate_route_files(self):
        subprocess.run(["duarouter", "-n", self.original_net_xml_filename, "--route-files", "output/trips.trips.xml", "-o", "output/original.rou.xml"])
        subprocess.run(["duarouter", "-n", self.tlp_net_xml_filename, "--route-files", "output/trips.trips.xml", "-o", "output/tlp.rou.xml"])


generator = RoutesGenerator("input/feup.net.xml","output/net.net.xml")
generator.generate_trips()
generator.generate_route_files()