import scan_inject as scan
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

class ChipViewer(object):
    """
    A curses application for real-time data from a chip.

    """
    
    def __init__(self):
        self._have_hardware = True
        self.scanner = None
        try:
            self.scanner = scan.Scanner("lt3maps/lt3maps.yaml")
        except:
            self._have_hardware = False
            def random_generator():
                while True:
                    num_hits = random.randint(0,64)
                    hits = range(64)
                    random.shuffle(hits)
                    hits = hits[:num_hits]
                    yield hits
                    time.sleep(1/18.0)
            self.scanner = random_generator()

    @staticmethod
    def _present_array(array):
        symbols = {
            0: u" ",
            1: u"\u2588",
        }
        symbols = {key: value.encode(code) for key, value in symbols.iteritems()}
        result = ""

        for number in array:
            result += symbols[number]
        return result

    @staticmethod
    def _get_offset(height, width):
        NUM_COLUMNS = 64
        NUM_ROWS = 18

        # want everything centered
        x_margin = (width - NUM_COLUMNS)/2
        y_margin = (height - NUM_ROWS)/2
        return (y_margin, x_margin)

    @staticmethod
    def _get_scan_results_hardware(scanner):
        col_hits = []
        scanner.reset()
        scanner.scan(1, 1)
        # make a matrix of pixel hits
        for i in range(len(scanner.hits[0]['data'])):
            col_hits.append(scanner.hits[0]['data'][i]['hit_rows'])
        return col_hits

    @staticmethod
    def _get_scan_results_software(scanner):
        col_hits = []
        for i in range(18):
            # make a matrix of pixel hits
            col_hits.append(next(scanner))
        return col_hits


    def _get_application(self, scan_function):
        def application(stdscr):
            curses.curs_set(0)
            stdscr.nodelay(1)
            # calculate the offset of the screen
            y_offset, x_offset = ChipViewer._get_offset(*stdscr.getmaxyx())
            stdscr.addstr(y_offset - 2, x_offset, "q to quit")
            stdscr.refresh()
            while True:
                # run the scan
                col_hits = scan_function(self.scanner)
                # process the results
                for i, col_hit in enumerate(col_hits):
                    col_diagram = np.zeros(64)
                    col_diagram[col_hit] = 1
                    # display the results
                    result_str = ChipViewer._present_array(col_diagram)
                    stdscr.addstr(i+y_offset, x_offset, result_str)
                stdscr.refresh()
                c = stdscr.getch()
                if c == ord('q'):
                    break
        return application

    def run_curses(self, scan_function=None):
        """
        Run the curses application with the given scanning function.

        The scan function should take a Scanner object as input and should
        output a list of lists, where each outer list is a column of the
        chip and each inner list lists the rows that have been hit. It will
        be run in an infinite loop.
        """
        if scan_function is None:
            if self._have_hardware:
                scan_function = ChipViewer._get_scan_results_hardware
            else:
                scan_function = ChipViewer._get_scan_results_software
        curses.wrapper(self._get_application(scan_function))

if __name__ == "__main__":
    app = ChipViewer()
    app.run_curses()
