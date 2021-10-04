# sample_processor.py

import runstats
import json
import datetime

"""
from fastapi import FastAPI, WebSocket
app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text())
        await websocket.send_text(f"Message text was: {data}")

"""


class Smoother:
    """
    Purpose: Smooth the samples from the arduino to remove jitter and noise.
    initialize the _smoother dict with a stats collector for each
    monitor_control_point (mc_point).  The stats collector will interpret 
    False as 0 and True as 1. Initialize the _former dict with steady state 
    values, all 0s.  TBD:   Instanciate the Websocket with host and Port
    """

    def __init__(self):
        self._smoother = {"A0": runstats.Statistics(),
                          "A1": runstats.Statistics(),
                          "A2": runstats.Statistics(),
                          "A3": runstats.Statistics(),
                          "A4": runstats.Statistics(),
                          "A5": runstats.Statistics(),
                          "D2": runstats.Statistics(),
                          "D3": runstats.Statistics(),
                          "D4": runstats.Statistics(),
                          "D5": runstats.Statistics(),
                          "D6": runstats.Statistics(),
                          "D7": runstats.Statistics(),
                          "D8": runstats.Statistics(),
                          "D9": runstats.Statistics(),
                          "D10": runstats.Statistics(),
                          "D11": runstats.Statistics(),
                          "D12": runstats.Statistics(),
                          "D13": runstats.Statistics(),
                          }

        self._former = {"A0": 0,
                        "A1": 0,
                        "A2": 0,
                        "A3": 0,
                        "A4": 0,
                        "A5": 0,
                        "D2": 0,
                        "D3": 0,
                        "D4": 0,
                        "D5": 0,
                        "D6": 0,
                        "D7": 0,
                        "D8": 0,
                        "D9": 0,
                        "D10": 0,
                        "D11": 0,
                        "D12": 0,
                        "D13": 0,
                        }

        #  self._websocket = WebSocket("ws://localhost:8000/ws")

    def reset(self):
        self.clear_all_stats()
        for k in self.former.items():
            self._former[k] = 0

    def add_sample(self, d):
        """
        samples are fed in as dict with key=mc_point, value= value 
        read by arduino (analog | digital). The value is pushed into
        the correct statscollector. 
        """
        for k, v in d.items():
            #  print(k,v)
            self._smoother[k].push(v)

    def clear_all_stats(self):
        """
        values in self._smoother are runstats collectors. v.clear initializes 
        the v collector for a new sample set.
        """
        for v in self._smoother.values():
            v.clear()

    def get_sample_size(self):
        """
        RETURNS the # of samples for key "A0". Assumes that all mc_points 
        share the same count. Since all 19 mc_points are pushed in turn for 
        each loop iteration by python firmata code, assumption is good.
        """
        return self._smoother["A0"].__len__()

    def get_smoothed_value(self, key):
        """
        RETURNS dict {key: mean}. For analog mc_points, mean is simple avg, 
        for digital mc_points, mean is rounded resulting in one of = [0 | 1]
        """
        if key.__contains__("A"):
            val = round(self._smoother[key].mean(), 3)  # to 3 decimal places
        else:
            val = round(self._smoother[key].mean())  # to nearest int
        return {key: val}

    def get_changes(self):
        """
        RETURNS a json array of dict. If the smoothed mc_point is different 
        from the former smoothed mc_point, the smoothed mc_point dict is added 
        to the changes list. The first dict is the datetimestamp. The slice 
        operator can truncate datetime decimal in seconds. Default is 6 
        decimal places ( or micro-seconds). The dts is followed by all of 
        the changed mc_points with their new values. So json dumps
         an array of objects (dicts).
        """
        changes = list()  # list of dicts
        dts = [{"datetime": str(datetime.datetime.now())}]
        changes.extend(dts)
        #  print(changes)
        for k, v in self._smoother.items():
            new_dict = self.get_smoothed_value(k)
            if new_dict[k] != self._former[k]:
                changes.extend([new_dict])
                self._former[k] = new_dict[k]
        return json.dumps(changes)


"""
    def transmit_changes(self, changes):
        self._websocket.send(json.dumps(changes))

    def transmit_msg(msg):
        self._websocket.send(msg)
"""
