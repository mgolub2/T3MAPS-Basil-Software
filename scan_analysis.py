import numpy as np
import pprint
import yaml
import time
import random
import curses
# Unicode support for curses
import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

have_hardware = True
scanner = None
try:
    import scan_inject as scan
    scanner = scan.Scanner("lt3maps/lt3maps.yaml")
except:
    have_hardware = False
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

def get_offset(height, width):
    NUM_COLUMNS = 64
    NUM_ROWS = 18

    # want everything centered
    x_margin = (width - NUM_COLUMNS)/2
    y_margin = (height - NUM_ROWS)/2
    return (y_margin, x_margin)

def get_scan_results(scanner):
    col_hits = []
    if have_hardware:
        scanner.reset()
        scanner.scan(1, 1)
        # make a matrix of pixel hits
        for i in range(len(scanner.hits[0]['data'])):
            col_hits.append(scanner.hits[0]['data'][i]['hit_rows'])
    else:
        for i in range(18):
            # make a matrix of pixel hits
            col_hits.append(next(scanner))

    return col_hits


def get_application(scan_function):
    def application(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(1)
        # calculate the offset of the screen
        y_offset, x_offset = get_offset(*stdscr.getmaxyx())
        stdscr.addstr(y_offset - 2, x_offset, "q to quit")
        stdscr.refresh()
        while True:
            # run the scan
            col_hits = scan_function(scanner)
            # process the results
            for i, col_hit in enumerate(col_hits):
                col_diagram = np.zeros(64)
                col_diagram[col_hit] = 1
                # display the results
                stdscr.addstr(i+y_offset, x_offset, present_array(col_diagram))
            stdscr.refresh()
            c = stdscr.getch()
            if c == ord('q'):
                break
    return application

def run_curses(scan_function=get_scan_results):
    """
    Run the curses application with the given scanning function.

    The scan function should take a Scanner object as input and should
    output a list of lists, where each outer list is a column of the
    chip and each inner list lists the rows that have been hit. It will
    be run in an infinite loop.
    """
    curses.wrapper(get_application(scan_function))

if __name__ == "__main__":
    run_curses()
