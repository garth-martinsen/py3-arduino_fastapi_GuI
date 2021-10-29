# file: signal_processing.py

import pdb
import time
import json
import requests
import datetime


class InputPin:
    """
    Creates an object which can be:
         sorted on sig_type
         updated with smoothed values,
         compared to former values
         encoded as json to persist to db.
         If pwm could be an input, also create a type "pwm" Later...
    """

    def __init__(self, name):
        self.name = name
        if name.upper().find('A') > -1:
            self.sig_type = "analog"
        if name.upper().find("D") > -1:
            self.sig_type = "digital"
        self.pin = int(name[1:])
        self.value = 0

    def __repr__(self):
        return f'{self.sig_type } {self.pin} {self.value}'


class ArduinoSignalProcessor:
    """
    ArduinoSignalProcessor performs the following for arduino signals:
        1. generates dictionaries that will facilitate processing
        2. segregates analog from digital signals to allow different smoothing.
        3. detects when changes have occurred in signal values.
        4. marshals the changes into json for transmission to database via HTTP
        5. sends http request to save json to db.
    """

    def initialize(self, config, Arduino, util, timestamp):
        """
        config contains: input_names, analog_num, digital_num , usb_port, url,
        input_names is a list of signal names eg: ["A0", "D2",  ...]
        RETURNS: independent dicts and lists by type(analog, digital).
        given the input_pins, creates dicts and lists for processing:
        apins is a List[InputPin] where InputPin.sig_type=analog
        dpins is a List[InputPin] where InputPin.sig_type=digital
        current_state values will later be updated with smoothed values
        and compared to former_state to trigger a signal change event
        """
        #  start timer for 'db_saved' secs.
        self.db_saved = timestamp
        print('Please wait ~10 seconds for initialization...')
        self.board = Arduino(config.usb_port)
        thread = util.Iterator(self.board)
        thread.start()
        time.sleep(1)
        print(f'board iterator thread is_alive: {thread.is_alive()}')

        self.src = config.src
        self.db_interval_lookup = config.db_interval_lookup
        self.analog_num_lookup = config.analog_num_lookup
        self.analog_num = config.initial_analog_num  # 10: averages 10 reads
        self.db_interval = config.initial_db_interval   # 60: saves ~every min
        self.analog_3sigma = config.analog_3sigma  # when 0, has no effect
        self.digital_num = config.digital_num  # if 5, requires 5 consecutive reads  # noqa: E501
        self.input_pins = config.input_names
        self.db_url = config.db_url
        self.apins = [InputPin(a) for a in self.input_pins if a.find("A") > -1]
        self.dpins = [InputPin(d) for d in self.input_pins if d.find("D") > -1]
        self.current_state = self.former_state = {}
        [self.current_state.update({p: InputPin(p).value})
         for p in self.input_pins]
        [self.former_state.update({p: InputPin(p).value})
         for p in self.input_pins]
        self.db_file_path = config.db_file_path
        print(f'data will be saved to file: {self.db_file_path} \
            via : {self.db_url}')

        print('Set up: PIN MODE VALUE')
        INPUT = 0   # pin mode
        self.setup_analog(INPUT)
        self.setup_digital(INPUT)

    def setup_analog(self, pin_mode):
        board = self.board
        for s in self.apins:
            pin = s.pin
            board.analog[pin].mode = pin_mode
            board.analog[pin].value = 0.0
            board.analog[pin].enable_reporting()
            print(f'         A{pin}, {board.analog[pin]._get_mode()},   {board.analog[pin].value}')  # noqa: E501

    def setup_digital(self, pin_mode):
        board = self.board
        for s in self.dpins:
            pin = s.pin
            board.digital[pin].mode = pin_mode
            board.digital[pin].value = 0
            board.digital[pin].enable_reporting()
            print(f'         D{pin}, {board.digital[pin]._get_mode()},   {board.digital[pin].value}')  # noqa: E501

    def set_db_interval(self, a2d):
        """
        config file defines dict(lookup) of a2d:seconds , copied to this class.
        this method collects all items that exceed the given a2d into tuples.
        SIDE-EFFECT: sets the seconds for db_interval between saves iaw a2d
        RETURNS Nothing.
        """
        gt = [(k, v) for k, v in self.db_interval_lookup.items() if k > a2d]
        self.db_interval = gt[0][1]

    def set_analog_num(self, a2d):
        """
        lookup of a2d:number (dict), copied from config file.
        this method collects all items that exceed the given a2d into tuples.
        RETURNS : Nothing
        SIDE-EFFECT: Sets the count for analog smoothing from 1st tuple in gt
        """
        gt = [(k, v) for k, v in self.analog_num_lookup.items() if k > a2d]
        self.analog_num = gt[0][1]

    def collect_inputs(self):
        """
        RETURNS: Nothing
        SIDE_EFFECT: current_state dict is updated with smoothed values.
        Collects enough reads for each type of signal to do the smoothing.
        Sets the analog_num and db_interval, each by lookup functions(a2d)
        """
        for apin in self.apins:
            a2d = self.smooth_analog(apin.pin)
            # sets values as functions of a2d
            self.set_analog_num(a2d)
            self.set_db_interval(a2d)
            self.current_state[apin.name] = a2d

        for dpin in self.dpins:
            val = self.smooth_digital(dpin.pin)
            self.current_state[dpin.name] = val

    def get_reader(self, type, pin, board):
        """
        Returns the proper reader as provided by board
        Override this method in subclass to mock readers
        """
        if type == 'digital':
            reader = board.digital[pin]
        elif type == 'analog':
            reader =  board.analog[pin]
        return reader

    def smooth_analog(self, pin):
        """
        RETURNS: smoothed value for a2d converted to A2D counts
        analog pin numbers can be any of [0-5] .
        """
        _sum = 0
        analog = self.get_reader('analog', pin, self.board)
        for i in range(self.analog_num):
            _sum += analog.read()
            time.sleep(.1)  # future study:find best sleep value for lowest noise.  # noqa: E501
        return round(_sum / self.analog_num * 1023)

    def smooth_digital(self, pin):
        """
        This method smooths for a single pin. pin is an int
        RETURNS: either [0|1] for the pin .Pins in range(2,14) are digital pins
        Unexpected change in value (prev !=curr) below, resets the counters.
        Winning counter is the one that exceeds num first.
        Result is similar to debouncer of yester-year. CAUTION, If bit stream
        alternates, so counters are constantly reset before num is reached,
        an infinite loop could result.
         """
        falseCount = trueCount = 0
        prev = curr = None
        num = self.digital_num
        digital = self.get_reader('digital', pin, self.board)

        while trueCount < num and falseCount < num:
            curr = digital.read()
            if curr == prev:
                if curr == 1:
                    trueCount += 1
                else:
                    falseCount += 1
            else:  # start over when value changes, first read is wasted
                falseCount = trueCount = 0
            prev = curr  # for next read compare
            time.sleep(.1)

        return int(trueCount > falseCount)

    def changed(self, ts):
        """
        compares all pins [digital|analog] in current_state vs former_state.
        ts is a float for time comparison.
        (time.time() or datetime.datetime.now().timestamp())
        If change conditions are met on any pin, Returns True else False,
        and updates Former_state[pin] to equal current_state[pin]
        Options to limit db size due to unworthy measurements:
        1. time passed since last db_saved < db_interval     -> Used
        2. analog changes less than 3 sigma considered noise -> Used
        3. a2d values outside of limits are ignored,         -> Not Used.
        Current usage: Only options 1,2 are applied but db_interval varies with
        a2d value and analog_3sigma is set to 0. so currently, only timing
        """
        changed = 0
        #  timing
        if ts - self.db_saved > self.db_interval:
            for p in self.apins:
                diff = self.current_state[p.name] - self.former_state[p.name]
                if abs(diff) >= self.analog_3sigma:  # now set to zero
                    changed = True
                    self.former_state[p.name] = self.current_state[p.name]

            for p in self.dpins:
                if self.current_state[p.name] != self.former_state[p.name]:
                    changed = True
                    self.former_state[p.name] = self.current_state[p.name]

        return changed

    def json_encode(self, datetimestamp):
        """
        RETURNS: json for the database save
        json will be like: {"A1": 997,"D2": false,...}. 
        It will reflect all input_names specified in the config
        """
        encoded = '{'
        encoded += f'"ts":"{datetimestamp}",'
        encoded += f'"src": "{self.src}",'

        for k, v in self.current_state.items():
            val = int(v)
            encoded += f'"{k}": {val},'
        return encoded[:-1] + '}'

    def update_db(self, datetimestamp):
        jd = self.json_encode(str(datetimestamp))
        print()
        print(f'sending to db: {jd}')
        # record the time of the db_save.
        self.db_saved = datetimestamp.timestamp()
        # post the json to url
        response = requests.post(self.db_url, data=jd)
        return response
