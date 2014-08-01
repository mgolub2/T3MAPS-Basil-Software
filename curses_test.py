import curses
import random
import numpy as np
import time
import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

def function():
    while True:
        num_hits = random.randint(0,64)
        hits = range(64)
        random.shuffle(hits)
        hits = hits[:num_hits]
        yield hits
        time.sleep(1/18.0)

scanner = function()

def present_array(array):
    symbols = {
        0: u" ",
        1: u"\u2588",
    }
    symbols = {key: value.encode(code) for key, value in symbols.iteritems()}
    result = ""

    for number in array:
        result += symbols[number]
    return result

def application(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.addstr(19, 0, "q to quit")
    stdscr.refresh()
    while True:
        for i in range(18):
            col_1_diagram = np.zeros(64)
            col_1_diagram[next(scanner)] = 1
            stdscr.addstr(i, 0, present_array(col_1_diagram))
        stdscr.refresh()
        c = stdscr.getch()
        if c == ord('q'):
            break

if __name__ == "__main__":
    curses.wrapper(application)
