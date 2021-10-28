# file: sampler.py

import config 
import signal_processor as p
from pyfirmata import Arduino, util
import datetime
import time
import requests

sigproc = p.ArduinoSignalProcessor()


def initialize():
    sigproc.initialize(config, Arduino, util, time.time())
    print(f'Started sampling at: {str(time.ctime())}')


def get_data():
    '''
    RETURNS: a data record which is a dict with  a timestamp, ts, and however 
    many InputPins were specified in the config.py file. Each InputPin has 
    3 attributes: sig_type, pin, value.  examples: for pins:
    ....'A1': ('analog', 1 , 978)
    ....'D2':('digital', 2, 1).  # bool is best modeled as 0|1 in this app
    The algorithm to determine if a signal has changed depends on 
    ....A2D noise for analogs sampling +/-3 sigma envelope
    ....digital signal transition (1->0 or 0->1)
    ....time from the last db save in seconds
    These values are specified in the config.py file. 
    This function is called upon a timeout in the GUI window.read(...).
    So the GUI is updated every time it calls processor.get_data() but the 
    db is updated only when it is called by the GUI AND 
    change criteria are met.
    '''
    sigproc.collect_inputs()
    dts = datetime.datetime.now()
    if sigproc.changed(dts.timestamp()):
        response = sigproc.update_db(dts)
        if response.ok:
            print(f'OK: {response.json()}')
    return {**sigproc.current_state, "ts": str(dts)}
