import scan_inject as scan
import matplotlib.pyplot as plt
import numpy as np
import pprint
import yaml
import multiprocessing
import time
import random

"""
data_file = open("out.yaml", 'r')
hit_data = yaml.load(data_file.read())
cycle_0 = hit_data[0]['data']
"""
scanner = None
try:
    scanner = scan.Scanner("lt3maps/lt3maps.yaml")
except IOError:
    def function():
        while True:
            num_hits = random.randint(0,64)
            hits = range(64)
            random.shuffle(hits)
            hits = hits[:num_hits]
            yield hits

    scanner = function()

time_to_sleep = 1

data = np.zeros(64)
axes = plt.axes(xlim=(0,64), ylim=(0,30))
line, = plt.plot(data)
plt.ion()
plt.ylim([0,30])
plt.show()
for i in range(3):
    col_1_hits = None
    try:
        scanner.hits = []
        scanner.scan(time_to_sleep, 1)

# make a matrix of pixel hits
        col_1_hits = scanner.hits[0]['data'][1]['hit_rows']

    except:
        col_1_hits = next(scanner)

    col_1_diagram = np.zeros(64)
    col_1_diagram[col_1_hits] = 1

    print col_1_diagram

    line.set_ydata(col_1_diagram)
    plt.draw()
    time.sleep(0.1)
    plt.pause(0.0001)

    """
    plt.bar(range(64), col_1_diagram, 1)
    plt.show()
    """


    # check out this website
    # http://stackoverflow.com/questions/19766100/real-time-matplotlib-plot-is-not-working-while-still-in-a-loop
