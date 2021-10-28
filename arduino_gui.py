#  file: arduino_gui.py
import PySimpleGUI as sg
import sampler
import pdb


def start_sampler():
    sampler.initialize()


def get_data():
    data = sampler.get_data()
    if data is not None:
        update_controls(data)


def update_controls(data):
    # Only show ts to the second

    window["TS"].update(data["ts"][:-7])
    window["A1"].update(data["A1"])
    window["D2"].update(data["D2"])
    window["D3"].update(data["D3"])


controls = [
    [sg.Text("D2"), sg.Input("0", size=(3, 1), key="D2"),
     sg.Text("D3"), sg.Input("0", size=(3, 1), key="D3")],
    [sg.Text("A1"), sg.Input("", size=(7, 1), key="A1")],
    [sg.Text("TS"), sg.Input("", size=(25, 1), key="TS")]
]

window = sg.Window("ArduinoPins", controls, return_keyboard_events=True,
                   size=(250, 80), finalize=True, keep_on_top=True)


start_sampler()

while True:
    event, values = window.read(timeout=1000)  # every second to get data.
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    get_data()
