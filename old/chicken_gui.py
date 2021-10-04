# file: chicken_gui.py

import PySimpleGUI as sg
#  import chicken_arduino as ca
import time
import pdb
import requests
import json


off_on = {False: "grey", True: "yellow"}


def update_analog():
    """
    analog Signal Change events in arduino processor cause a call to this 
    function. key is a string that matches the key in the controls listed 
    below. val will update the text entry field with the new value.
    """
    response = requests.get('http://127.0.0.1:8000/analogs/')
    if response.ok:
        analogs = response.json()
        key = analogs[-1]["name"]
        val = analogs[-1]["value"]
        #  print(analogs)
    window[key].update(value=val)


def update_digital():
    """
    digital change event in arduino causes a call to this function.
    key matches the keys in the controls below. background color
    of the control will change based on boolean state.
    """
    response = requests.get('http://127.0.0.1:8000/digitals')
    if response.ok:
        digitals = response.json()
        key = digitals[-1]["name"]
        val = digitals[-1]["value"]
        state = off_on.get(val)
    window[key].update(background_color=state)


controls = [
    [sg.Text("Dig"), sg.Text("Dig"), sg.Text("Analog")],
    [sg.Input("D2", s=(3, 1), background_color="grey", key="D2", ),
     sg.Input("D3", s=(
         3, 1), background_color="grey", key="D3", ),
     sg.Text("A0"), sg.Input("", size=(7, 1), key="A0")],
    [sg.Input("D4", size=(3, 1), background_color="grey", key="D4",),
     sg.Input("D5", size=(
         3, 1), background_color="grey", key="D5",),
     sg.Text("A1"), sg.Input("", size=(7, 1), key="A1")],
    [sg.Input("D6", size=(3, 1), background_color="grey", key="D6", ),
     sg.Input("D7", size=(3, 1), background_color="grey",
              key="D7",),
     sg.Text("A2"), sg.Input("", size=(7, 1), key="A2")],
    [sg.Input("D8", size=(3, 1), background_color="grey",
              key="D8",),
     sg.Input("D9", size=(3, 1), background_color="grey",
              key="D9",),
     sg.Text("A3"), sg.Input("", size=(7, 1), key="A3")],
    [sg.Input("D10", size=(3, 1), background_color="grey",
              key="D10",),
     sg.Input("D11", size=(3, 1), background_color="grey",
              key="D11",),
     sg.Text("A4"), sg.Input("", size=(7, 1), key="A4")],
    [sg.Input("D12", size=(3, 1), background_color="grey",
              key="D12",),
     sg.Input("D13", size=(3, 1), background_color="grey",
              key="D13",),
     sg.Text("A5"), sg.Input("", size=(7, 1), key="A5")],
]

input_frm = sg.Frame(
    "Inputs",
    controls,)
layout = [[input_frm]]

window = sg.Window("ChickenCoop", layout, return_keyboard_events=True,
                   size=(750, 500), finalize=True)  # resizable=True,


"""  the arduino samples, smooths, detects changes, saves to db 
and calls update on this gui. 

THIS NEEDS WORK!! DB IS UPDATED ON ONE SIGNAL AT A TIME, THE UPDATE TO THE GUI 
SHOULD BE ON ONE SIGNAL AT A TIME. SO LET CA RETURN THE JSON DICT WITH NAME 
AND VALUE AND THIS LOOP WILL UPDATE THE GUI ONE SIGNAL AT A TIME.
"""
while True:
    event, values = window.read()
    #  pdb.set_trace()
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    update_analog()
    update_digital()
