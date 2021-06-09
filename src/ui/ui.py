# hello_psg.py

from typing import Text
import PySimpleGUI as sg

options_column = [
    [
        sg.Text("OSM file"),
        sg.In(size=(25, 1), enable_events=True, key="-OSM-"),
        sg.FileBrowse(),
    ],
    [
        sg.Text("TLP option 1"),
        sg.In(size=(25, 1), enable_events=True, key="-OPTION-"),
    ],
    [
        sg.Text("UAMS option 2"),
        sg.In(size=(25, 1), enable_events=True, key="-OPTIONS-"),
    ],
]


log_column = [
    [
        sg.Text("Logs"),
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(40, 20), key="-LOGS-"
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
window = sg.Window("Demo", layout)

# Create an event loop
while True:
    event, values = window.read()
    # End program if user closes window or
    # presses the OK button
    if event == "Exit" or event == sg.WIN_CLOSED:
        break

window.close()