import os
import sys

import traci
import traci.constants as tc
import sumolib


if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


class SimulationManager(object):

    def __init__(self, sumo_cfg_filename):

        sumoBinary = "C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui"

        sumoConfig = ["-c", sumo_cfg_filename, "-S"]

        self.sumoCmd = [sumoBinary, sumoConfig[0],
                        sumoConfig[1], sumoConfig[2]]

    def run_simulation(self, simulation_time):
        print("Starting the TraCI server...")
        traci.start(self.sumoCmd)

        step = 0
        while step < simulation_time:
            # advance the simulation
            traci.simulationStep()
            step += 1
            # if emergency breaking or a collision occurs stop the simulation

        print("\nStopping the TraCI server...")
        traci.close()
