# test_quick_signal_processor.py

import pytest
import mock_config
import datetime
import signal_processor
import pdb
from pyfirmata import Arduino, util, Pin


""" ======Testing requirements==========
X indicates that a test exists and passes. NA means didn't bother.
InputPin:
    X def __init__(self, name):
    NA  def __repr__(self):

ArduinoSignalProcessor:
    X def initialize(self, config, Arduino, util, timestamp):
    X def setup_analog(self, pin_mode):
    X def setup_digital(self, pin_mode):
    X def set_db_interval(self, a2d):
    X def set_analog_num(self, a2d):
    X def collect_inputs(self):
    X def get_reader(self, type, pin, board):
    X def smooth_analog(self, pin):
    X def smooth_digital(self, pin):
    X def changed(self, ts):
    X def json_encode(self, datetimestamp):
    X def update_db(self, dts):

"""


def gen(lst):
    for x in lst:
        yield x


digital = {2: list(bin(14987979559889010687))[2:],  # 64 bits: 1100 then all 1s
           3: list(bin(13835058055282163712))[2:]}  # 64 bits: 1100 then all 0s


class read_analog_mock:
    """
    for now even tho the pin is passed in it does not affect the mock
    Design: Split the samples symetrically around zero. If num is odd,
    leave the central zero in the sequence, else remove it. This will always
    result in sum = 0 , hence average = 0. 
    """

    def __init__(self, num, pin):
        n1 = num // 2
        n2 = num - n1 + 1
        self.a = [x for x in range(- n1, n2)]
        if num % 2 == 0:
            self.a.remove(0)
        self.an = gen(self.a)

    def read(self):
        return self.an.__next__()


class read_digital_mock:
    def __init__(self, num, pin):
        """
        num (int) is smoothing number. pin:int is the digital pin #
        Test pin 2 for True and pin3 for False
        """
        # pdb.set_trace()
        self.d = digital[pin]
        self.digit = gen(self.d)

    def read(self):
        return int(self.digit.__next__())


class MockSignalProcessor(signal_processor.ArduinoSignalProcessor):

    def get_reader(self, type, pin, board):
        d_readers = {2: read_digital_mock(5, 2), 3: read_digital_mock(5, 3)}
        # pdb.set_trace()
        if type == 'digital':
            return d_readers[pin]
        elif type == 'analog':
            return read_analog_mock(10, 1)


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


@pytest.fixture
def mocked_http_response():
    return MockResponse('{"test": "passed"}', 200)


@pytest.fixture
def mockdatetime():
    """
    Happy New Year 2021!
    """
    return datetime.datetime(2021, 1, 1, 0, 0, 0, 000000)


@pytest.fixture
def mockArduino(mocker):
    return mocker.patch('pyfirmata.Arduino')


@pytest.fixture
def mockutil(mocker):
    return mocker.patch('pyfirmata.util')


@pytest.fixture
def mock_board(mockArduino):
    return mockArduino(mock_config.usb_port)

@pytest.fixture
def real_proc(mockdatetime):
    proc = signal_processor.ArduinoSignalProcessor()
    proc.initialize(mock_config, Arduino, 
        util, mockdatetime.timestamp())
    return proc


@pytest.fixture
def mock_proc(mocker, mockArduino, mockutil, mockdatetime, mock_board):
    mock_proc = signal_processor.ArduinoSignalProcessor()
    mock_proc.initialize(mock_config, mockArduino,
                        mockutil, mockdatetime.timestamp())
    mock_proc.src = 'test'
    mock_proc.board = mockArduino(mock_config.usb_port)

    return mock_proc


@pytest.fixture
def mock_readers(mockArduino, mockutil, mockdatetime):

    mockproc = MockSignalProcessor()
    mockproc.initialize(mock_config, mockArduino, mockutil, mockdatetime.timestamp())  # noqa: E501
    return mockproc


# -------------Tests ---------------------


def test_init_InputPina():
    ip = signal_processor.InputPin('A1')
    assert(ip.sig_type == 'analog' and ip.pin == 1 and ip.value == 0)


def test_init_InputPind():
    ip = signal_processor.InputPin('D12')
    assert(ip.sig_type == 'digital' and ip.pin == 12 and ip.value == 0)


def test_repr():
    ip = signal_processor.InputPin('D12')
    r = str(ip)
    assert r == 'digital 12 0'


def test_initialize(mocker, mock_proc, mockdatetime):
    assert mock_proc.src == mock_config.src
    assert mock_proc.db_interval == mock_config.initial_db_interval
    assert mock_proc.db_url == mock_config.db_url
    assert mock_proc.analog_num == mock_config.initial_analog_num
    assert mock_proc.digital_num == mock_config.digital_num
    assert mock_proc.analog_num_lookup == mock_config.analog_num_lookup
    assert mock_proc.db_interval_lookup == mock_config.db_interval_lookup
    assert mock_proc.analog_3sigma == mock_config.analog_3sigma
    assert mock_proc.db_file_path == mock_config.db_file_path
    assert mock_proc.input_pins == mock_config.input_names
    assert mock_proc.current_state.get('A1') == 0.0
    assert mock_proc.current_state.get("D2") == 0
    assert mock_proc.current_state.get("D3") == 0
    assert mock_proc.former_state.get("A1") == 0.0
    assert mock_proc.former_state.get("D2") == 0
    assert mock_proc.former_state.get("D3") == 0
    assert mock_proc.db_saved == mockdatetime.timestamp()
    assert len(mock_proc.apins) == 1
    assert len(mock_proc.dpins) == 2


def test_setup_analog(mock_proc, mock_board):
    INPUT = 0
    mock_proc.board = mock_board
    mock_proc.apins = [signal_processor.InputPin('A1')]

    mock_proc.setup_analog(0)

    assert mock_board.analog[1].mode == INPUT
    assert mock_board.analog[1].value == 0
    assert mock_board.analog[1].reporting


def test_setup_digital(mock_proc, mock_board):
    INPUT = 0  # INPUT
    mock_proc.board = mock_board
    mock_proc.dpins = [signal_processor.InputPin("D2"), signal_processor.InputPin("D3")]  # noqa: E501
    mock_proc.setup_digital(INPUT)

    assert mock_board.digital[2].mode == INPUT
    assert mock_board.digital[2].value == 0
    assert mock_board.digital[2].reporting
    assert mock_board.digital[3].mode == INPUT
    assert mock_board.digital[3].value == 0
    assert mock_board.digital[3].reporting

def test_set_db_interval(mock_proc):

    mock_proc.db_interval_lookup = mock_config.db_interval_lookup

    mock_proc.set_db_interval(25)
    assert mock_proc.db_interval == 30
    mock_proc.set_db_interval(923)
    assert mock_proc.db_interval == 30
    mock_proc.set_db_interval(250)
    assert mock_proc.db_interval == 30


def test_set_analog_num(mock_proc):
    mock_proc.analog_num_lookup = mock_config.analog_num_lookup
    # input values are a2d counts
    mock_proc.set_analog_num(25)
    assert mock_proc.analog_num == 10
    mock_proc.set_analog_num(250)
    assert mock_proc.analog_num == 10
    mock_proc.set_analog_num(950)
    assert mock_proc.analog_num == 10


def test_collect_inputs(mock_proc, mocker):
    mocker.patch("signal_processor.ArduinoSignalProcessor.smooth_analog",
                 return_value=307)
    mocker.patch("signal_processor.ArduinoSignalProcessor.smooth_digital",
                 return_value=1)
    mocker.patch("signal_processor.ArduinoSignalProcessor.set_analog_num")
    mocker.patch("signal_processor.ArduinoSignalProcessor.set_db_interval")
    a1 = 1
    d2 = 2
    d3 = 3
    a2d = 307
    # pdb.set_trace()

    mock_proc.collect_inputs()

    assert mock_proc.smooth_analog.call_count == 1
    assert mock_proc.smooth_digital.call_count == 2
    assert mock_proc.smooth_analog.called_once_with(a1)
    assert mock_proc.smooth_digital.called_with(d2)
    assert mock_proc.smooth_digital.called_with(d3)
    assert mock_proc.set_analog_num.called_with(a2d)
    assert mock_proc.set_db_interval.called_with(a2d)
    # pdb.set_trace()
    assert mock_proc.current_state['A1'] == 307
    assert mock_proc.current_state['D2'] == 1


def test_get_mock_reader(mock_readers, mocker):
    reader = mock_readers.get_reader('analog', 1, mock_readers.board)

    assert type(reader) == read_analog_mock
   
    reader = mock_readers.get_reader('digital', 2, mock_readers.board)
    assert type(reader) == read_digital_mock 

def test_get_real_reader(real_proc):
    """
    In order for this test to work, the usb must be plugged into the arduino
    """
    reader = real_proc.get_reader('analog',1, real_proc.board)
    assert type(reader)== Pin
 
    reader = real_proc.get_reader('digital',2, real_proc.board)
    assert type(reader)==  Pin


def test_smooth_analog(mock_readers, mocker):
    """
    The mock_reader for analog will generate a sequence that sums to 0
    in order to have realistic number for a2d, a bias of 3 is passed in
    so that when the summing is complete, the _sum=3. This gives an average
    of 0.3 when analog_num=10. Converting 0.3 to a2d by multiplying by 1023
    yields an a2d of 307. 

    mocker.patch("signal_processor.ArduinoSignalProcessor.smooth_analog",
                 return_value=307)
    mocker.patch("signal_processor.ArduinoSignalProcessor.smooth_digital",
                 return_value=1)
     """
    mocker.patch("signal_processor.ArduinoSignalProcessor.set_analog_num")
    mocker.patch("signal_processor.ArduinoSignalProcessor.set_db_interval")
    apins = [signal_processor.InputPin('A1')]
    for p in apins:
        val = mock_readers.smooth_analog(p.pin, 3)
        assert val == 307
  


def test_smooth_digital(mock_readers):
    dpins = [signal_processor.InputPin("D2"), signal_processor.InputPin("D3")]  # noqa: E501
    val = [-1, -1, -1, -1]
    for pin in dpins:
        # pdb.set_trace()
        val[pin.pin] = mock_readers.smooth_digital(pin.pin)

    print(val)
    assert val[2] == 1
    assert val[3] == 0


def test_changed(mock_proc, mockdatetime):
    mock_proc.db_saved = mockdatetime.timestamp()
    
    mock_proc.former_state['A1']= 300
    mock_proc.former_state['D2']= 1
    mock_proc.former_state['D3']= 0
    mock_proc.current_state['A1']= 307
    mock_proc.current_state['D2']= 0
    mock_proc.current_state['D3']= 1
    
    # pdb.set_trace()
    assert mock_proc.changed(mockdatetime.timestamp() + 90)

    assert mock_proc.former_state['A1']== 307
    assert mock_proc.former_state['D2']== 0
    assert mock_proc.former_state['D3']== 1
    assert mock_proc.former_state ==  mock_proc.current_state

def test_json_encode(mock_proc, mockdatetime):
    # pdb.set_trace()
    mock_proc.current_state['A1'] = 307
    mock_proc.current_state['D2'] = 1
    mock_proc.current_state['D3'] = 0

    jsn = mock_proc.json_encode(mockdatetime)
    assert jsn == '{"ts":"2021-01-01 00:00:00","src": "test","A1": 307,"D2": 1,"D3": 0}'  # noqa: E501


def test_update_db(mocker, mock_proc, mockdatetime, mocked_http_response):
    '''
    mocker.patch('signal_processor.ArduinoSignalProcessor.json_encode',
                 return_value='{"good":"encoding"}')
                 '''
    mocker.patch('signal_processor.requests.post',
                 return_value=mocked_http_response)
    mock_proc.current_state['A1'] = 307
    mock_proc.current_state['D2'] = 1
    mock_proc.current_state['D3'] = 0

    response = mock_proc.update_db(mockdatetime)

    # mock_proc.json_encode.assert_called_once()
    signal_processor.requests.post.called_once()
    assert response.status_code == 200
    assert response.json() == '{"test": "passed"}'
