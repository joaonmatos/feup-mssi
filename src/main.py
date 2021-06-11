

import os, sys
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:   
    sys.exit("please declare environment variable 'SUMO_HOME'")

sumoBinary = "C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui"
sumoConfig = ["-c", "network.sumocfg", "-S"]

sumoCmd = [sumoBinary, sumoConfig[0], sumoConfig[1], sumoConfig[2]]

import traci
import traci.constants as tc
import sumolib


# STATE LISTENER CLASS
class StateListener(traci.StepListener):
    def __init__(self, vehicleIds, emergencyBreakThreshold=-4.0):
        self.vehicleIds = vehicleIds
        self.emergencyBreakThreshold = emergencyBreakThreshold
        self.vehicles = {}
        self.emergencyBreak = False
        self.collision = False

    def step(self, t=0):
        self.retrieveState()
        self.printState()
        self.checkEmergencyBreak()
        self.checkCollision()
        # indicate that the state publisher should stay active in the next step
        return True

    def retrieveState(self):
        # receive vehicle data
        for vehicleId in self.vehicleIds:
            self.vehicles[vehicleId] = traci.vehicle.getSubscriptionResults(vehicleId)
            self.vehicles[vehicleId].rerouteTraveltime()
            
    def printState(self):
        # print vehicle data
         for vehicleId in self.vehicleIds:
             vehicle = self.vehicles[vehicleId]
             if vehicle is not None:
                 print("%s vel_t: %.2f m/s acc_t-1: %.2f m/s^2 dist: %.2f" % (vehicleId, vehicle[tc.VAR_SPEED], vehicle[tc.VAR_ACCELERATION], traci.lane.getLength(vehicle[tc.VAR_LANE_ID]) - vehicle[tc.VAR_LANEPOSITION]))
    
    def checkCollision(self):
        # if SUMO detects a collision (e.g. teleports a vehicle) set the collision flag
        if (traci.simulation.getStartingTeleportNumber() > 0):
            print("\nCollision occured...")
            self.collision = True

    def checkEmergencyBreak(self):
        # if any vehicle decelerates more than the emergencyBreakThreshold set the emergencyBreak flag
        for vehicleId in self.vehicleIds:
            vehicle = self.vehicles[vehicleId]
            if vehicle is not None:
                if vehicle[tc.VAR_ACCELERATION] < self.emergencyBreakThreshold:
                    print("\nEmergency breaking required...")
                    self.emergencyBreak = True




# MAIN PROGRAM

print("Starting the TraCI server...")
traci.start(sumoCmd) 


print("Constructing a StateListener...")

step = 0
while step < 20:
    # advance the simulation
    print("\nsimulation step: %i" % step)
    traci.simulationStep()
    step += 1
    # if emergency breaking or a collision occurs stop the simulation
    if stateListener.emergencyBreak or stateListener.collision:
        break

if stateListener.emergencyBreak or stateListener.collision:
    print("\nScenario failed...")
else:
    print("\nScenario succeeded...")

print("\nStopping the TraCI server...")
traci.close()
