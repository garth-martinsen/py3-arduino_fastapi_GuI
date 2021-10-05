# file: sampler.py

import config as c
import signal_processor as p
from pyfirmata import Arduino, util
import datetime

ap = p.ArduinoSignalProcessor()


def initialize():
    ap.initialize(c, Arduino, util)


def get_data():
    '''
    RETURNS: a data record which is a dict with  a timestamp, ts, and however 
    many InputPins were specified in the config.py file. Each InputPin has 
    3 attributes: sig_type, pin, value.  examples: for pins:
    ....'A1': ('analog', 1 , 978)
    ....'D2':('digital', 2, True).
    The algorithm to determine if a signal has changed depends on 
    ....A2D noise for analogs sampling +/-3 sigma envelope
    ....digital signal transition (True->False or False->True)
    ....time from the last db save 
    These values are set in the config.py file. 
    This function is called upon a timeout in the GUI window.read(...).
    So the GUI is updated every time it calls processor.get_data() but the 
    db is updated only when it is called by the GUI AND 
    change criteria are met.
    '''
    ap.collect_inputs()
    if ap.changed():
        ap.update_db()
    return {**ap.current_state, "ts": str(datetime.datetime.now())}
