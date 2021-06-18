from typing import Dict
import xml.etree.ElementTree as ET


class TripInfoStats:
    def __init__(self, avg_travel_time: float, total_distance: float) -> None:
        self.att = avg_travel_time
        self.d = total_distance

    def get_att(self) -> float:
        return self.att

    def get_total_distance(self) -> float:
        return self.d

    def __repr__(self) -> str:
        return f'TlpInfoStats(ATT: {self.att}, Total Distance: {self.d})'

    def __str__(self) -> str:
        return self.__repr__()


def process_trip_info(path_to_file: str) -> TripInfoStats:
    tree = ET.parse(path_to_file)
    tripinfos = tree.getroot()
    distance = 0.0
    duration = 0.0
    counter = 0
    for tripinfo in tripinfos:
        counter += 1
        distance += float(tripinfo.attrib["routeLength"])
        duration += float(tripinfo.attrib["duration"])
    return TripInfoStats(duration / counter, distance)


class GadStats:
    def __init__(self, ground_distance: float, air_distance: float) -> None:
        self.gtd = ground_distance
        self.atd = air_distance

    def get_ground_distance(self) -> float:
        return self.gtd

    def get_air_distance(self) -> float:
        return self.atd

    def get_atd(self) -> float:
        if self.gtd is not 0.0:
            return self.atd / self.gtd
        else:
            return self.gtd

    def __repr__(self) -> str:
        return f'GAD Stats(GAD {self.get_atd()})'

    def __str__(self) -> str:
        return self.__repr__()


def process_edge_info(path_to_file: str) -> GadStats:
    tree = ET.parse(path_to_file)
    meandata = tree.getroot()

    ground = 0.0
    air = 0.0

    for interval in meandata:
        if interval.attrib["id"][-4:] != "uams":
            continue
        for edge in interval:
            if edge.attrib["sampledSeconds"] == "0.00":
                continue
            if edge.attrib["id"][0:15] == "TLP_to_TLP_edge":
                air += float(edge.attrib["speed"]) * \
                    float(edge.attrib["sampledSeconds"])
            else:
                ground += float(edge.attrib["speed"]) * \
                    float(edge.attrib["sampledSeconds"])

    return GadStats(ground, air)


class TlpStats:
    def set_num_in(self, n: int) -> None:
        self._in = n

    def get_num_in(self) -> int:
        return self._in

    def set_num_out(self, n: int) -> None:
        self.out = n

    def get_num_out(self) -> int:
        return self.out

    def __repr__(self) -> str:
        return f'TlpStats(in:{self._in}, out:{self.out})'

    def __str__(self) -> str:
        return self.__repr__()


def process_tlp_uses(path_to_file: str) -> Dict[str, TlpStats]:
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


class MetricsProcessor:
    def __init__(self, path_to_folder, experiment_id) -> None:
        self.prefix = path_to_folder
        self.id = experiment_id

    def run(self):
        self.trips = process_trip_info(f"{self.prefix}/tripinfo_{self.id}.xml")
        self.gad = process_edge_info(f"{self.prefix}/edges_{self.id}.xml")
        self.tlp = process_tlp_uses(f"{self.prefix}/detectors_{self.id}.xml")

    def get_trip_info(self):
        return self.trips

    def get_ground_air_distance(self):
        return self.gad

    def get_tlp_stats(self):
        return self.tlp
