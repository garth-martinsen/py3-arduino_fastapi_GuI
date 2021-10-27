# file: mock_config.py
# DO NOT MODIFY THIS FILE. IT IS USED FOR TESTING AND MUST REMAIN AS IT IS FOR TESTS TO PASS.  # noqa: E501

src = 'test'  # what microcontroller is generating the signals

input_names = ["A1", "D2", "D3"]  # what pins are going to be sampled for this app  # noqa: E501

#  **************** Lookups ********************************************
#  Lookup for number of samples to be averaged, key: A2D  value: num
analog_num_lookup = {25: 10, 50: 10, 100: 10, 2048: 10}   # for testing
db_interval_lookup = {30: 30, 100: 30, 200: 30, 400: 30, 500: 30, 2048: 30}  # for testing  # noqa: E501

#  **************** Values *********************************************

initial_db_interval = 60         # seconds
# following is for info only. Change it for your path. The actual path is determined by startup of server.  # noqa: E501
db_file_path = '/Users/garth/Programming/python3/py3-arduino_fastapi_GuI/sql_app/signals.db'  # noqa: E501

initial_analog_num = 10

analog_3sigma = 0   # to relax this constraint, set it to 0

digital_num = 5

usb_port = '/dev/cu.usbmodem14301'

db_url = 'http://127.0.0.1:8000/pins/'
# for later work using nosql on a free public platform, ids are for me only
deta_db_url = 'https://sfwfom.deta.dev'
deta_projectId = 'b0uggz3e'
deta_microId = '58935fb8-1266-40bb-9499-c833071ce576'
