import xml.etree.ElementTree as ET
import subprocess

class TlpMutator():

    def getPlainXML(self, filename):
        #os.system("netconvert " + "--sumo " + filename + " --plain-output-prefix")
        subprocess.run(["netconvert", "--sumo-net-file",  filename ,"--plain-output-prefix"])    
    
    def storePlainXML(self):
      
    # netconvert --node-files=MyNodes.nod.xml --edge-files=MyEdges.edg.xml \
    #   --connection-files=MyConnections.con.xml --type-files=MyTypes.typ.xml \
    #   --output-file=MySUMONet.net.xml
        subprocess.run(["netconvert", "--node-files=true.nod.xml", "--edge-files=true.edg.xml", "--connection-files=true.con.xml","--tllogic-files=true.tll.xml"])    

    def __init__(self, net_xml_filename):
        self.xml_tree = ET.parse(net_xml_filename)
        self.xml_root = self.xml_tree.getroot()
        boundary = self.xml_root.find("location").get("convBoundary")
        self.min_x, self.max_x, self.min_y, self.max_y = boundary.split(",")
        self.getPlainXML(net_xml_filename)

    #Density in n_of_TLPs/km^2
    def generate_mutated_XML(self, density):

        # <junction id="leftBottom" type="priority" x="0.00" y="50.00" incLanes="leftTop_to_leftBottom_0 middleBottom_to_leftBottom_0" intLanes=":leftBottom_0_0 :leftBottom_1_0" shape="-3.20,53.20 3.20,53.20 3.20,46.80">
        #     <request index="0" response="00" foes="00" cont="0"/>
        #     <request index="1" response="00" foes="00" cont="0"/>
        # </junction>

        junction = ET.SubElement(self.xml_root, 'junction')
        request = ET.SubElement(junction, 'request')
        junction.set('id', 'TLP1')
        junction.set('type', 'priority')
        junction.set('x', '10.00')
        junction.set('y', '10.00')
        junction.set('incLanes', 'leftTop_to_leftBottom_0')
        junction.set('intLanes', ':leftBottom_1_0')
        junction.set('intLanes', 'TLP1')
        junction.set('shape', 'TLP1')
        #self.xml_root.append("")
        print(self.min_x)
        print(self.max_x)
        print(self.min_y)
        print(self.max_y)
        

tlp_mutator = TlpMutator("network.net.xml")
tlp_mutator.generate_mutated_XML(1)
tlp_mutator.storePlainXML()