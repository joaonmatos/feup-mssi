# hello_psg.py

import threading
from tkinter.constants import S
from typing import Text
import PySimpleGUI as sg
import queue
import numpy as np

from simulation.orchestrator import Orchestrator

options_column = [
    [
        sg.Text("OSM file"),
        sg.In(size=(25, 1), enable_events=True, key="-OSM-"),
        sg.FileBrowse(),
    ],
    [
        sg.Text('_'*30)
    ],
    [
        sg.Text("Simulation time"),
        sg.Slider([500, 1000],
         size=(20,15),
         orientation='horizontal',
         font=('Helvetica', 12))
    ],
    [
        sg.Text('_'*30)
    ],
    [
        sg.Text("Simulated trips range")
        
    ],
    [
        sg.Text("Maximum"),
        sg.Slider([10, 50000],
         size=(20,15),
         orientation='horizontal',
         font=('Helvetica', 12))
    ],
    [
        sg.Text("Minimum"),  
        sg.Slider([10, 50000],
         size=(20,15),
         orientation='horizontal',
         font=('Helvetica', 12))
    ],
    [
        sg.Text("Steps"),    
        sg.Spin([i for i in range(1,10)], initial_value=1),
    ],
    [
        sg.Text('_'*30)
    ],
    [
        sg.Text("UAMS Ratio")
        
    ],
    [
        sg.Text("Maximum"),
        
        sg.Slider(range=(0.00, 1.00), resolution=.01,  orientation='horizontal'),
    ],
    [
        sg.Text("Minimum"),  
        sg.Slider(range=(0.00, 1.00), resolution=.01,  orientation='horizontal'),
    ],
    [
        sg.Text("Steps"),    
        sg.Spin([i for i in range(1,10)], initial_value=3),
    ],
    [
        sg.Text('_'*30)
    ],
    [
        sg.Text("Number of Take-off/Landing Points (TLPs)")
        
    ],
    [
        sg.Text("Maximum"),
        sg.Spin([4, 9, 16, 25],
         size=(4,4),
         font=('Helvetica', 12))
    ],
    [
        sg.Text("Minimum"),
        sg.Spin([4, 9, 16, 25],
         size=(4,4),
         font=('Helvetica', 12))
    ],
    [
        sg.OK(), sg.Cancel(),
    ],
]


log_column = [
    [
        sg.Text("Logs"),
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(40, 30), key="-LOGS-"
        )
    ],
]

# ----- Full layout -----
layout = [
    [
        sg.Column(options_column),
        sg.VSeperator(),
        sg.Column(log_column),
    ]
]
# Create the window
window = sg.Window("Demo", layout).Finalize()

log_queue = queue.Queue(maxsize=0)

def data_gatherer():
    osm_filename = values["-OSM-"]
    simulation_time = values[0]
    
    trips_max = values[1]
    trips_min = values[2]
    trips_steps = values[3]
    if trips_max <= trips_min:
        sg.popup('Maximum trips must be greater than minimum trips')
        return
        
    if trips_steps == 1:
        trips_range = [trips_max]
    else:
        trips_range = np.arange(int(trips_min), int(trips_max+1), int((trips_max-trips_min)/(trips_steps-1)))

    uams_max = values[4]
    uams_min = values[5]
    uams_steps = values[6]
    if uams_max <= uams_min:
        sg.popup('Maximum UAMS Ratio must be greater than minimum UAMS Ratio')
        return

    if uams_steps == 1:
        uams_range = [uams_max]
    else:
        uams_range = np.arange(uams_min, uams_max + 0.1, ((uams_max-uams_min)/(uams_steps-1)))

    tlp_max = values[7]
    tlp_min = values[8]
    if tlp_min > tlp_max:
        sg.popup('Maximum number of TLPs must be greater or equal to minimum number of TLPs')
        return    
    
    tlp_range = []
    for value in [4,9,16,25]:
        if value >= tlp_min and value <= tlp_max:
            tlp_range.append(value)

    orchestrator = Orchestrator(osm_filename, simulation_time, trips_range, uams_range, tlp_range, log_queue)
    simulations_tread = threading.Thread(target=orchestrator.run_simulations())
    simulations_tread.start()
    return


logs = []
# Create an event loop
while True:
    while not log_queue.empty():
            newlog = log_queue.get()
            log_queue.task_done()
            if newlog:
                logs.append(newlog)
                window.FindElement('-LOGS-').Update(values = logs)
                continue
    event, values = window.read()
    # End program if user closes window or
    # presses the OK button
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    if event == "OK":
        data_gatherer()
        
        
window.close()
