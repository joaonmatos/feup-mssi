import queue
import time
import math
import simulation.tlpMutator as tlpm
import simulation.routesGenerator as rg
from itertools import product
from simulation.simulationManager import SimulationManager


class Orchestrator(object):

    def __init__(self, osm_filename, simulation_time, trips_set, uams_set, tlps_set, log_queue):
        self.osm_filename = osm_filename
        self.simulation_time = simulation_time
        self.trips_set = trips_set
        self.uams_set = uams_set
        self.tlps_set = tlps_set
        self.log_queue = log_queue
        self.tlp_mutator = tlpm.TlpMutator()
        self.detector_edges = {}

    def run_simulations(self):
        self.log_queue.put('Simulation parameters')
        self.log_queue.put(f'OSM network: {self.osm_filename}')
        self.log_queue.put(f'Simulation time: {self.simulation_time}')
        self.log_queue.put(f'Trips: {self.trips_set}')
        self.log_queue.put(f'UAMSs: {self.uams_set}')
        self.log_queue.put(f'TLPs: {self.tlps_set}')

        self.tlp_mutator.importOSM(
            self.osm_filename, "simulation/output/original.net.xml")

        for tlps in self.tlps_set:
            self.generate_net_files(tlps)

        self.grid_create_files()
        self.grid_run_games()
        return

    def grid_create_files(self):
        for current_params in product(self.tlps_set, self.trips_set, self.uams_set):
            self.generate_route_files(
                current_params[0], current_params[1], current_params[2])
        return

    def generate_net_files(self, tlps):
        self.log_queue.put("Generating network with " + str(tlps) + " TLPs")
        self.tlp_mutator.deconstruct_net_file(
            "simulation/output/original.net.xml")
        in_edges, out_edges = self.tlp_mutator.generate_mutated_XML(
            int(math.sqrt(tlps)))
        self.tlp_mutator.storePlainXML(
            f'simulation/output/mutated{tlps}.net.xml')
        self.tlp_mutator.cleanup()
        self.detector_edges[tlps] = [in_edges, out_edges]
        return

    trips_generated = []
    added_uams = []

    def generate_route_files(self, tlps, trips, uams):

        route_generator = rg.RoutesGenerator(
            "simulation/output/original.net.xml", f'simulation/output/mutated{tlps}.net.xml')

        if trips not in self.trips_generated:
            self.trips_generated.append(trips)
            self.log_queue.put(
                "Generating trip file with " + str(trips) + " TLPs")
            route_generator.generate_trips(
                f'simulation/output/trips{trips}.trips.xml', self.simulation_time, trips)

        trip_file_id = str(trips) + str(uams)
        if trip_file_id not in self.added_uams:
            self.trips_generated.append(trip_file_id)
            route_generator.add_UAMS(
                uams, f'simulation/output/trips{trips}.trips.xml',
                f'simulation/output/trips{trips}_ratio_{uams}.trips.xml')

        route_generator.generate_route_files(
            f'simulation/output/trips{trips}_ratio_{uams}.trips.xml',
            f'simulation/output/routes-trips{trips}_uams{uams}_tlps{tlps}.rou.xml')

        route_generator.generate_sumocfg('simulation/template.sumocfg',
                                         f'../output/mutated{tlps}.net.xml',
                                         f'../output/routes-trips{trips}_uams{uams}_tlps{tlps}.rou.xml',
                                         f'../additional_files/add-trips{trips}_uams{uams}_tlps{tlps}.xml',
                                         f'../metrics/tripinfo-trips{trips}_uams{uams}_tlps{tlps}.xml',
                                         self.simulation_time,
                                         f'simulation/simcfg/config-trips{trips}_uams{uams}_tlps{tlps}.sumocfg')
        print("Detectror Edges" + str(self.detector_edges))
        route_generator.generate_additional_file(
            f'simulation/additional_files/add-trips{trips}_uams{uams}_tlps{tlps}.xml',
            self.detector_edges[tlps][0], self.detector_edges[tlps][1], self.simulation_time,
            f'../metrics/detectors_trips{trips}_uams{uams}_tlps{tlps}.xml', f'../metrics/edges_trips{trips}_uams{uams}_tlps{tlps}.xml')

    def grid_run_games(self):
        for current_params in product(self.tlps_set, self.trips_set, self.uams_set):
            self.run_simulation(
                f'simulation/simcfg/config-trips{current_params[1]}_uams{current_params[2]}_tlps{current_params[0]}.sumocfg')
        return

    def run_simulation(self, cfg_filename):
        sim_manager = SimulationManager(cfg_filename)
        sim_manager.run_simulation(self.simulation_time)
        return
