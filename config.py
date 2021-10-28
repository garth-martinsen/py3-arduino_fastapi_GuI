# file: config.py

src = 'uno' #  what microcontroller is generating the signals

input_names = ["A1", "D2", "D3"]  # what pins are going to be sampled for this app  # noqa: E501

#  **************** Lookups ********************************************
#  Lookup for number of samples to be averaged, key: A2D  value: num

analog_num_lookup = {25: 100, 50: 75, 100: 25, 2048: 25}

#  Lookup for arduino db_interval, key:A2D, value:seconds
# function returns:  0-99:240   100-199:60  200-399:30  400-1023: 60
db_interval_lookup = {30: 300, 100: 240, 200: 60, 400: 30, 500: 60, 2048: 240}

#  **************** Values *********************************************

initial_db_interval = 60         # seconds

initial_analog_num = 10

analog_3sigma = 0   # to remove this constraint, set it to 0

digital_num = 5

usb_port = '/dev/cu.usbmodem14301'

db_url = 'http://127.0.0.1:8000/pins/'
# following is for info only. Change it for your path. The actual path is determined by startup of server.  # noqa: E501
db_file_path = '/Users/garth/Programming/python3/py3-arduino_fastapi_GuI/sql_app/signals.db'  # noqa: E501

# for later work using nosql on a free public platform, ids are for me only
deta_db_url = 'https://sfwfom.deta.dev'
deta_projectId = 'xxxxxxx'
deta_microId = 'xxxxxxxxxxxxxxxxxxxx'

