# file: plot_gui.py

import PySimpleGUI as sg
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # noqa: E501
import matplotlib.patches as mpatches
from passlib.context import CryptContext
from jose import JWTError, jwt
import pdb
# ------------------------------- This is to include a matplotlib figure in a Tkinter canvas  # noqa: E501


def avg_by(lst, num):
    '''
    reduces and smooths a list of integers by averaging groups of num values
    RETURNS a list[int]
    when the iteration reaches the end of the list, it will insert zeros to 
    to replace missing ints to make up the last elements of avg[].
    Later, I will figure out how to get a good average for the last element of 
    avg, or perhaps throw it away because it is distorted.
    def range(start, stop, step=num):
    '''
    avgd = []
    a = 0
    b = a + num
    for i in range(0, len(lst), num):
        avgd.append(round(sum(lst[a:b]) / num))
        a = b
        b = a + num
        # -1 is to prevent a severe drop off at end.
        l1 = round(len(lst) / num - 1)
    return avgd[:l1]


def every_nth(lst, num):
    '''
    ts, D2, D3, are not averaged like A1. They are thinned by selecting every 
    nth value. 
    '''
    selected = []
    for i in range(0, len(lst), num):
        selected.append(lst[i])
    return selected


def my_sort(e):
    return e['ts']
#  'raw',0


def do_plot(how, many):
    headers_dict = {"Authorization": "Bearer garth",
                    "accept": "application/json"}
    response = requests.get('http://127.0.0.1:8000/pins',
                            headers=headers_dict)
    a1 = d2 = d3 = 0
    if response.ok:
        pins = response.json()
        num = len(pins)
        pins.sort(key=my_sort)
        date = pins[0]['ts'][0:10]
        window['-Date-'].update(f'Date: {date}')
        window['-Samples-'].update(f'Samples: {num}')

        # get raw numbers from the db
        x1 = [p['ts'][11:19] for p in pins]
        y1 = [p['A1'] for p in pins]
        y2 = [p['D2'] for p in pins]
        y3 = [p['D3'] for p in pins]

        # smoothing
        if how == 'avg':
            a1 = avg_by(y1, many)
            ts = every_nth(x1, many)[:len(a1)]
            d2 = every_nth(y2, many)[:len(a1)]
            d3 = every_nth(y3, many)[:len(a1)]
        else:
            ts = x1
            a1 = y1
            d2 = y2
            d3 = y3

    fig, ax = plt.subplots()
    DPI = fig.get_dpi()
    # --you have to play with this size to reduce the movement error when the mouse hovers over the figure, it's close to canvas size  # noqa: E501
    fig.set_size_inches(404 * 2 / float(DPI), 404 / float(DPI))
    # -------------------------------
    plt.title('Arduino pins vs Time')
    # plot Analogs
    color = 'tab:red'
    ax.set_xlabel('TimeStamp')
    ax.set_ylabel('A1', color=color)
    ax.tick_params(axis='y', labelcolor=color)
    ax.plot(ts, a1, color=color)
    red_patch = mpatches.Patch(color='red')
    ax.grid()

    # plot Digitals
    ax2 = ax.twinx()

    color = 'tab:blue'
    ax2.set_ylabel('digital', color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.plot(ts, d2, color=color)
    blue_patch = mpatches.Patch(color='blue')

    color = 'tab:green'
    ax2.plot(ts, d3, color=color)
    ax2.xaxis.set_major_locator(plt.MultipleLocator(round(len(ts) / 7)))
    green_patch = mpatches.Patch(color='green')
    plt.sca(ax)
    fig.tight_layout()

    # plt.show()
    # ----Instead of plt.show()

    draw_figure_w_toolbar(
        window['fig_cv'].TKCanvas, fig, window['controls_cv'].TKCanvas)


def draw_figure_w_toolbar(canvas, fig, canvas_toolbar):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if canvas_toolbar.children:
        for child in canvas_toolbar.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(fig, master=canvas)
    figure_canvas_agg.draw()
    toolbar = Toolbar(figure_canvas_agg, canvas_toolbar)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)


class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)


# ------------------------------- PySimpleGUI CODE

layout = [
    [sg.T('Graph: Arduino Pins')],
    [sg.B('Plot'), sg.T('num:'), sg.Input("", size=(5, 1), key='-Num-'),
     sg.B('Plot_Avg'), sg.B('Exit')],
    [sg.T('Controls:')],
    [sg.Canvas(key='controls_cv')],
    [sg.T('Figure:'), sg.T('', key='-Date-'), sg.T('', key='-Samples-')],
    [sg.Column(
        layout=[
            [sg.Canvas(key='fig_cv',
                       # it's important that you set this size
                       size=(400 * 2, 400)
                       )]
        ],
        background_color='#DAE0E6',
        pad=(0, 0)
    )],
    # [sg.B('Alive?')
]

window = sg.Window('Graph with controls', layout)

while True:
    event, values = window.read()
    print(event, values)
    if event in (sg.WIN_CLOSED, 'Exit'):  # always,  always give a way out!
        break
    if event == 'Plot':
        do_plot('raw', 0)
    if event == 'Plot_Avg':
        do_plot('avg', int(values['-Num-']))
window.close()
