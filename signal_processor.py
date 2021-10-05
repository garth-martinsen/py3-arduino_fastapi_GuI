# file: signal_processing.py

import pdb
import time
import json
import requests
import datetime
from fastapi.encoders import jsonable_encoder
# import chicken_gui as cg


class InputPin:
    """
    Creates an object which can be:
         sorted on sig_type
         updated with smoothed values, 
         compared to former values
         encoded as json to persist to db.
    """

    def __init__(self, name):
        self.name = name
        if name.upper().find('A') > -1:
            self.sig_type = "analog"
        if name.upper().find("D") > -1:
            self.sig_type = "digital"
        self.pin = int(name[1])
        self.value = 0

    def __repr__(self):
        return f'{self.sig_type } {self.pin} {self.value}'

    def __str__(self):
        return f'{self.name}  {self.value}'


class ArduinoSignalProcessor:
    """
    ArduinoSignalProcessor performs the following for arduino signals:
        1. generates dictionaries that will facilitate processing
        2. segregates analog from digital signals to allow different smoothing.
        3. detects when changes have occurred in signal values.
        4. marshals the changes into json for transmission to database via HTTP
    """

    def initialize(self, config, Arduino, util):
        """
        config contains: input_names, analog_num, digital_num , usb_port
        input_pins is a list of signal names eg: ["A0", "D2",...]
        RETURNS: 2 independent dicts and 2 lists.
        given the input_pins, creates 2 dicts and 2 lists for processing:
        apins is a List[InputPin] where InputPin.sig_type=analog
        dpins is a List[InputPin] where InputPin.sig_type=digital
        current_state values will later be updated with smoothed values
        and compared to former_state to cause a signal change event
        """
        self.src = config.src
        self.db_interval_lookup = config.db_interval_lookup
        self.analog_num_lookup = config.analog_num_lookup
        self.analog_num = config.initial_analog_num  # 100: averages 100 reads
        self.db_interval = config.initial_db_interval   # 60: saves ~every min

        self.analog_3sigma = config.analog_3sigma
        self.digital_num = config.digital_num
        self.input_pins = config.input_names
        input_pins = config.input_names
        self.db_url = config.db_url
        apins = [InputPin(a) for a in input_pins if a.find("A") > -1]
        dpins = [InputPin(d) for d in input_pins if d.find("D") > -1]
        current_state = {}
        former_state = {}
        [current_state.update({p: InputPin(p)}) for p in input_pins]
        [former_state.update({p: InputPin(p)}) for p in input_pins]
        
        self.apins = apins
        self.dpins = dpins
        self.current_state = current_state
        self.former_state = former_state
        #  start timer on db_saved so that after 60 seconds can do db_save.
        self.former_state.update({'db_saved': time.time()})
        print('Please wait for 10 seconds for initialization...')
        self.board = Arduino(config.usb_port)
        thread = util.Iterator(self.board)
        thread.start()
        time.sleep(1)
        print(f'board iterator thread is_alive: {thread.is_alive()}')
        print('Set up: PIN MODE VALUE')
        INPUT = 0   # pin mode

        self.setup_analog(INPUT)
        self.setup_digital(INPUT)
        db_file_path = '/Users/garth/Programming/python3/py3-arduino_fastapi_GuI/sql_app/signals.db'  # noqa: E501
        print(f'saved to sqlite file: {db_file_path} via : {self.db_url}')

    def setup_analog(self, IO):
        board = self.board
        for s in self.apins:
            pin = s.pin
            board.analog[pin].mode = IO
            board.analog[pin].value = 0.0
            board.analog[pin].enable_reporting()
            print(f'         A{pin}, {board.analog[pin]._get_mode()},   {board.analog[pin].value}')  # noqa: E501

    def setup_digital(self, IO):
        board = self.board
        for s in self.dpins:
            pin = s.pin
            board.digital[pin].mode = IO
            board.digital[pin].value = False
            board.digital[pin].enable_reporting()
            print(f'         D{pin}, {board.digital[pin]._get_mode()},   {board.digital[pin].value}')  # noqa: E501

    def set_db_interval(self, a2d):
        """
        config file holds lookup of a2d:seconds (dict), copied to this class.
        this method collects all items that exceed the given a2d into tuples.
        RETURNS Nothing.
        SIDE-EFFECT: sets the seconds for arduino loop delay 
        """
        gt = [(k, v) for k, v in self.db_interval_lookup.items() if k > a2d]
        self.db_interval = gt[0][1]

    def set_analog_num(self, a2d):
        """
        lookup of a2d:number (dict), copied from config file.
        this method collects all items that exceed the given a2d into tuples.
        RETURNS : Nothing
        SIDE-EFFECT: Sets the count for analog smoothing in 1st tuple 
        """
        gt = [(k, v) for k, v in self.analog_num_lookup.items() if k > a2d]
        self.analog_num = gt[0][1]

    def collect_inputs(self):
        for sig in self.apins:
            self.smooth_analog(sig)
        for sig in self.dpins:
            self.smooth_digital(sig)

    def smooth_analog(self, signal):
        """
        RETURNS: nothing. 
        SIDE_EFFECT: current dict is updated with average_of_n analog samples 
        converted to A2D counts
        """
        sum = 0.0
        pin = int(signal.pin)
        #  waste one read to clear anomalies
        self.board.analog[pin].read()

        for i in range(self.analog_num):
            sum += self.board.analog[pin].read()
            time.sleep(.1)
        a2d = round(sum / self.analog_num * 1023)
        self.set_analog_num(a2d)     # sets value for next smooth
        # sets value for arduino loop
        self.set_db_interval(a2d)

        """set values as A2D counts"""
        self.current_state[signal.name].value = a2d

    def smooth_digital(self, signal):
        """
        RETURNS: nothing. 
        SIDE_EFFECT: Updates current_state with pin.value [True|False]
        signal isA InputPin, with name, pin, sig_type, value
        Unexpected change in value (last !=curr) resets the counters.
        Winning counter is the one that exceeds num first.
         """
        falseCounter = trueCounter = 0
        last = curr = None
        num = self.digital_num
        #  pdb.set_trace()
        while trueCounter < self.digital_num and falseCounter < self.digital_num:
            curr = self.board.digital[signal.pin].read()
            """ 
            if no value change from last, continue to count else reset counters
            and try again
            """
            #  pdb.set_trace()
            if curr == last:
                if curr:
                    trueCounter += 1   # True counter
                else:
                    falseCounter += 1   # False counter
            else:  # start over when value changes
                falseCounter = trueCounter = 0
            last = curr  # for next read compare
            time.sleep(.1)
        #  pdb.set_trace()
        if trueCounter > falseCounter:
            val = True
        else:
            val = False
        # update pin.value with value in the current dict.
        self.current_state[signal.name].value = val

    def changed(self):
        """
        compares all pins [digital|analog] in current_state vs former_state.
        If any changes are found, AND sufficient time has passed, 
        changed is returned as True else False.
        if changed: Former_state will be updated to equal current_state.
        analog changes less than 3 sigma are not classified as a change.
        Latest: 3 sigma is set to 0 and limits are not applied.
                """
        # maxLimit = 1001
        # minLimit = 29
        thresh = self.analog_3sigma
        changed = False
        #  Check to see if too soon to save
        now = time.time()
        #. pdb.set_trace()
        if now - self.former_state['db_saved'] < self.db_interval:
            return False
        else:
            for p in self.apins:
                curr = self.current_state[p.name].value
                former = self.former_state[p.name].value
                diff = curr - former
                if abs(diff) >= thresh:  # noqa: E501
                    changed = True
                    self.former_state[p.name].value = self.current_state[p.name].value  # noqa: E501
            for p in self.dpins:
                if self.current_state[p.name].value != self.former_state[p.name].value:  # noqa: E501
                    changed = True
                    self.former_state[p.name].value = self.current_state[p.name].value  # noqa: E501

        return changed

    def json_encode(self):
        """
        RETURNS: json for the database save
        json will be like: {"A1": 997,"D2": false}. 
        It will reflect all input_names specified in the config
        """
        encoded = '{'
        ts = f'"ts":"{str(datetime.datetime.now())}",'
        encoded += ts
        src = f'"src": "{self.src}",'
        encoded += src
        for k, v in self.current_state.items():
            if isinstance(v.value, bool):
                val = str(v.value).lower()
            else:
                val = v.value
            encoded += f'"{k}": {val},'
        return encoded[:-1] + '}'

    def update_db(self):
        jd = self.json_encode()
        print()
        print(f'sending to db: {jd}')
        # record the time of the db_save.
        self.former_state.update({'db_saved': time.time()})

        response = requests.post(self.db_url, data=jd)  # noqa: E501
        if response.ok:
            print(f'OK: {response.json()}')
