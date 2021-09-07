# file: chicken_arduino.py
"""
This script will setup the arduino, receive its signals, smooth the
analog values by average_of_TBD, watch for changes. When the value changes
by more than 3 sigma, the changed values will be encoded into a JSON object
(a, dict) with  timestamp, name, value. For Digitals, value will be Integer.
For Analogs, value will be a Float. The JSON object will be sent over the
websocket to the server.
"""
import pyfirmata as pf
from pyfirmata import Arduino, util
import time
import datetime
import requests
import pdb   # comment this out or remove for production

""" initialize arrays for comparison to find change events """
current_analog = [0, 0, 0, 0, 0, 0]
former_analog = [0, 0, 0, 0, 0, 0]

# 0,1 reserved for rxtx
current_digital = [None, None, False, False, False, False, False,
                   False, False, False, False, False, False]
former_digital = [None, None, False, False, False, False, False, False,
                  False, False, False, False, False, False]


OPENING = 0
CLOSING = 1
OPENED = 2
CLOSED = 3
door_state = {OPENING: False, CLOSING: False, OPENED: False, CLOSED: False}


def initialize_door_state():
    door_state[OPENED] = True


def get_door_action(curr_digital, curr_analog, door_state):
    if door_state[CLOSED] and curr_analog[1] > 350:
        print('Door was closed and is opening')
        door_state[OPENED] = True
        door_state[CLOSED] = False
        print('Now the door is opened.')
    if door_state[OPENED] and curr_analog[1] < 350:
        print('Door was opened and is closing')
        door_state[CLOSED] = True
        door_state[OPENED] = False
        print('Now the door is closed')


def get_url(name):
    if name.find('A') > -1:
        url = 'http://127.0.0.1:8000/analogs/'
    elif name.find('D') > -1:
        url = 'http://127.0.0.1:8000/digitals/'
    return url


def save_to_db(url, json_result):
    #  pdb.set_trace()
    response = requests.post(url, data=json_result)
    if response.ok:
        print(response.status_code, response.json())      # Check status_code + json response  # noqa: E501
    else:
        print(response.status_code)


def build_json(name, value):
    """
    Called on a signal change event with the name of the signal
    (analog or digital) and the value (float or bool) . Builds
    valid json expression with datetimestamp, src (eg: uno), 
    and value. 
    """
    dts = str(datetime.datetime.now())
    j = f'"ts": "{dts}", "src": "uno",  "name": "{name}", "value": {value}'
    j2 = '{' + j + '}'
    return j2


def detect_analog_change(pin, current, former):
    """
    current is set of 6 (A0-A5) latest smoothed A2D values
    former  is set of 6 (A0-A5) former smoothed A2D values
    """
    diff = abs(current[pin] - former[pin])
    
    json_result = None
    if diff > 6:
        former[pin] = current[pin]
        name = f'A{pin}'
        value = current[pin]
        json_result = build_json(name, value)
        #  pdb.set_trace()
        save_to_db(get_url(name), json_result)
    return json_result


def detect_digital_change(pin, current, former):
    """
    current is set of 11(D2-D13) latest smoothed digital values
    former  is set of 11(D2-D13) former smoothed digital values
    A digital change event occurs when current[pin]!= former[pin]
    """
    json_result = None
    if current[pin] != former[pin]:
        name = f'D{pin}'
        value = current[pin]
        former[pin] = current[pin]
        json_result = build_json(name, value.tolower())
        save_to_db(get_url(name), j2)
    return json_result


def setup_analog(pin, IO):
    board.analog[pin].mode = IO
    board.analog[pin].value = 0.0
    board.analog[pin].enable_reporting()
    print(
        f'setup A{pin}, {board.analog[pin]._get_mode()}, {board.analog[pin].value}')  # noqa: E501


def setup_digital(pin, IO):
    board.digital[pin].mode = IO
    board.digital[pin].value = 0
    board.digital[pin].enable_reporting()
    print(
        f'setup D{pin}, {board.digital[pin]._get_mode()}, {board.digital[pin].value}')  # noqa: E501


def smooth_analog(pin, reps, current, former):
    """
    returns mean a2d count over reps repetitions rounded to an integer
    """
    sum = 0.0
    for i in range(reps):
        sum += board.analog[pin].read()
        time.sleep(.01)
    current[pin] = round(sum / reps * 1023)
    #  pdb.set_trace()
    detect_analog_change(pin, current, former)


def smooth_digital(pin, reps, current, former):
    """
    sets a value [0|1] in current[pin] when consecutive reps are all the same value.
    A flip-flop change in value resets the counters for 0 and 1.
    """
    cnt0 = cnt1 = 0
    last = curr = None

    while cnt0 < reps and cnt1 < reps:
        curr = board.digital[pin].read()
        #  if no flipflop, continue to count else reset counters and try again
        if curr == last:
            if curr:
                cnt1 += 1
            else:
                cnt0 += 1
        # start over when flip flop occurs
        else:
            cnt1 = cnt0 = 0
        time.sleep(.01)
    # set the smoothed digital value in the current List.
    if cnt0 > cnt1:
        val = False
    else:
        val = True
    current[pin] = val
    #  pdb.set_trace()
    detect_digital_change(pin, current, former)


#   ===============Setup=======================
print("Wait 5 seconds for setup...")
board = Arduino('/dev/cu.usbmodem14301')
thread = util.Iterator(board)
thread.start()
time.sleep(1)
print(f'thread is_alive: {thread.is_alive()}')
# set all analog pins A0 to A5 to mode:INPUT and initialize to 0.0
print('pin, mode, value')

initialize_door_state()
setup_analog(1, pf.INPUT)
setup_digital(2, pf.INPUT)
#  pdb.set_trace()

print("setup complete")
while True:
    analog_change = smooth_analog(1, 25, current_analog, former_analog)
    #  update_analog(analog_change['name'], analog_change['value'])
    digital_change = smooth_digital(2, 5, current_digital, former_digital)
    #  update_digital(digital_change['name'], digital_change['value'])
    #  TBD: get_door_action(current_digital, current_analog, door_state)
    time.sleep(1)
