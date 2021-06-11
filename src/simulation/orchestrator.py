import queue
import time
import math
import simulation.tlpMutator as tlpm
import simulation.routesGenerator as rg
from itertools import product

class Orchestrator(object):
    
    def __init__(self, osm_filename, simulation_time, trips_set, uams_set, tlps_set, log_queue):
        self.osm_filename = osm_filename
        self.simulation_time = simulation_time
        self.trips_set = trips_set
        self.uams_set = uams_set
        self.tlps_set = tlps_set
        self.log_queue = log_queue
        self.tlp_mutator = tlpm.TlpMutator();


    def run_simulations(self):
        self.log_queue.put('Simulation parameters')
        self.log_queue.put(f'OSM network: {self.osm_filename}')
        self.log_queue.put(f'Simulation time: {self.simulation_time}')
        self.log_queue.put(f'Trips: {self.trips_set}')
        self.log_queue.put(f'UAMSs: {self.uams_set}')
        self.log_queue.put(f'TLPs: {self.tlps_set}')

        self.tlp_mutator.importOSM(self.osm_filename, "simulation/output/original.net.xml")
        
        self.log_queue.put(str(self.tlps_set))
        for tlps in self.tlps_set:
            self.generate_net_files(tlps)

        self.sim_grid_search()
        
        
        return
    
    def sim_grid_search(self):
        for current_params in product(self.tlps_set, self.trips_set, self.uams_set):
            self.log_queue.put("Running simulation for parameters:" + str(current_params))
            self.generate_route_files(current_params[0], current_params[1], current_params[2])
        return


    def generate_net_files(self, tlps):
        self.log_queue.put("Generating network with " + str(tlps) + " TLPs")
        self.tlp_mutator.deconstruct_net_file("simulation/output/original.net.xml")
        self.tlp_mutator.generate_mutated_XML(int(math.sqrt(tlps)))
        self.tlp_mutator.storePlainXML(f'simulation/output/mutated{tlps}.net.xml')
        self.tlp_mutator.cleanup()
        return
    
    trips_generated = []
    def generate_route_files(self, tlps, trips, uams):
        route_generator = rg.RoutesGenerator(f'simulation/output/mutated{tlps}.net.xml', "simulation/output/original.net.xml")
        if trips not in self.trips_generated: 
            self.trips_generated.append(trips)
            self.log_queue.put("Generating trip file with " + str(trips) + " TLPs")
            route_generator.generate_trips(f'simulation/output/trips{trips}.trips.xml', self.simulation_time, trips)
        
    
    def run_simulation(self):
        pass