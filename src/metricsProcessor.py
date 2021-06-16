import xml.etree.ElementTree as ET

class TlpStats:
    def set_num_in(self, n):
        self._in = n
    
    def get_num_in(self):
        return self._in

    def set_num_out(self, n):
        self.out = n
    
    def get_num_out(self):
        return self.out

    def __str__(self):
        return f'TlpStats(in:{self._in}, out:{self.out})'

def process_tlp_uses(path_to_file):
    tree = ET.parse(path_to_file)
    detector_node = tree.getroot()
    stats = {}
    for interval_node in detector_node:
        id = interval_node.attrib["id"]
        n = int(interval_node.attrib["nVehEntered"])
        if id[-3:] == "_in":
            tlp_id = id[4:-3]
            tlp = TlpStats()
            tlp.set_num_in(n)
            stats[tlp_id] = tlp
        else:
            tlp_id = id[4:-4]
            stats[tlp_id].set_num_out(n)
    return stats
    
# 
def process_edge_info(path_to_file):
    tree = ET.parse(path_to_file)
    meandata_node = tree.getroot()
    interval_nodes = meandata_node.findall("interval")
    stats = {}
    
    # Default vType
    for interval_node in interval_nodes[0]:
        pass
    
    
    # UAMS vType
    for interval_node in interval_nodes[1]:
        pass

    return

print(process_tlp_uses("./src/simulation/metrics/detectors_trips951_uams0.63_tlps4.xml"))
