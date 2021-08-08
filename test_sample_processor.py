# file: test_sample_processor.py

import smoother
#  import runstats
import random
import json
#  from fastapi import Websocket

import pytest


@pytest.fixture
def smoother():
    return smoother.Smoother()


analogs = [f"A{i}" for i in range(0, 6)]
digis = [f"D{i}" for i in range(2, 14)]

inputs = {"A0": [2.123, 3.456, 1.999, 4.678, 5.256, ],
          "A1": [3.451, 3.672, 4.253, 5.684, 5.335, ],
          "A2": [22.456, 23.991, 21.989, 22.345, 24.678, ],
          "A3": [18.332, 19.443, 17.554, 18.665, 18.778, ],
          "A4": [7.221, 7.332, 7.443, 8.554, 9.115, ],
          "A5": [12.112, 13.223, 12.334, 12.445, 13.556, ],
          "D2": [0, 0, 1, 0, 1, ],
          "D3": [1, 1, 1, 0, 0, ],
          "D4": [0, 0, 0, 1, 1, ],
          "D5": [0, 0, 1, 0, 1, ],
          "D6": [1, 1, 1, 0, 0, ],
          "D7": [0, 0, 0, 1, 1, ],
          "D8": [0, 0, 1, 0, 1, ],
          "D9": [0, 0, 1, 0, 1, ],
          "D10": [0, 0, 1, 1, 1, ],
          "D11": [0, 0, 1, 0, 1, ],
          "D12": [0, 0, 1, 0, 1, ],
          "D13": [0, 0, 0, 1, 1, ],
          }
means = {"A0": 3.502, "A1": 4.479, "A2": 23.092,
         "A3": 18.554, "A4": 7.933, "A5": 12.734,
         'D2': 0, 'D3': 1, 'D4': 0, 'D5': 0, 'D6': 1,
         'D7': 0, 'D8': 0, 'D9': 0, 'D10': 1, 'D11': 0,
         'D12': 0, 'D13': 0}


# initialize former dictionaries to 0.0 and False respectively
analog_former = [{a: 0.0} for a in analogs]
digital_former = [{d: False} for d in digis]

"""
TO BE TESTED (?):
   def __init__(self):
    def add_sample(self, d):
    def get_sample_size(self, key):
    def get_smoothed_value(self, key):
    def get_changes(self):
    def transmit_changes(self, changes):
    def transmit_msg(msg):
"""


def test_init(smoother):
    assert isinstance(smoother._smoother, dict)
    assert isinstance(smoother._former, dict)
    #  assert isinstance(smoother._websocket, WebSocket)


def test_add_sample(smoother, mc_point):
    smoother._smoother[mc_point].clear()
    for x in analog_inputs[mc_point]:
        smoother.add_sample({mc_point: x})
    assert smoother._smoother[mc_point].__len__() == 5


def test_get_smoothed_value(smoother, mc_point):
    smoother._smoother[mc_point].clear()
    for x in analog_inputs[mc_point]:
        smoother.add_sample({mc_point: x})
    assert smoother._smoother[mc_point].mean() == means[mc_point]


def test_smooth_all(smoother):
    for k, v in smoother._smoother.items():
        v.clear()
    for k, v in inputs.items():
        for x in v:
            smoother.add_sample({k: x})
    for k, v in smoother._smoother.items():
        print(json.dumps(smoother.get_smoothed_value(k)))


"""
def test_detect_changes():
    apoint = "A2"
    dpoint = "D2"
    rsa = smoother.analog_smoother[apoint]
    for k in analog_inputs:
        rsa.push(analog_inputs[k])
    rsd = smoother.digital_smoother[dpoint]
    for k in digital_inputs:
        smoother[k].push(digital_inputs[k])
    d = smoother.detect_changes(analog_former, digital_former,
                                smoother.analog_smoother, smoother.digital_smoother)  # noqa: E501
    print(d)


def test_digital_smoother():
    point = "D6"
    rs = smoother.digital_smoother[point] 
    for d in digital_inputs["D6"]:
        rs.push(d)
    assert rs.mean() > 0.5


TESTS 
for s in a0_samples:
    analog_smoother["A0"].push(s)
    print(detect_analog_change(
        analog_former["A0"], analog_smoother["A0"].mean(), thresh))

for s in a1_samples:
    analog_smoother["A1"].push(s)
    print(detect_analog_change(
        analog_former["A1"], analog_smoother["A1"].mean(), thresh))

print(analog_former)
"""
