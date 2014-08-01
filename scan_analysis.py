import scan_inject as scan
import logging
import numpy as np
import pprint
import yaml
import time
import random
import curses
import functools
# Unicode support for curses
import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

class ScanFunctionReturn(object):
    """
    Manage return values from the scan function.

    """

    def __init__(self, timestamp, column_hits, keep_going):
        self.timestamp = timestamp
        self.column_hits = column_hits
        self.keep_going = keep_going

class ChipViewer(object):
    """
    A curses application for real-time data from a chip.

    """
    
    def __init__(self):
        self.persistence_history = np.zeros((18,64))
        self.event_history = []
        self.history_file = None

    def _save_history(self):
        if self.history_file is not None:
            with open(self.history_file, 'w') as outfile:
                for i, scan_result in enumerate(self.event_history):
                    outfile.write("BEGIN SCAN #%i" % i)
                    outfile.write("\n")
                    outfile.write(str(scan_result.timestamp))
                    outfile.write("\n")
                    for column in scan_result.column_hits:
                        for row in column:
                            outfile.write(str(row))
                            outfile.write(" ")
                        outfile.write("\n")
                    outfile.write("END SCAN #%i" %i)
                    outfile.write("\n")

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
        scanner.chip.import_TDAC("tune_results.yaml")
        scanner.scan(1, 1, 58)
        # make a matrix of pixel hits
        for i in range(len(scanner.hits[0]['data'])):
            col_hits.append(scanner.hits[0]['data'][i]['hit_rows'])
        num_hits = 0
        for index, column in enumerate(col_hits):
            for row in column:
                pixel = scanner.chip._pixels[index][row]
                num_hits += 1
        logging.debug("%i hits", num_hits)
        return ScanFunctionReturn(time.time(), col_hits, True)

    @staticmethod
    def _get_scan_results_software(scanner):
        col_hits = []
        for i in range(18):
            # make a matrix of pixel hits
            col_hits.append(next(scanner))
        return ScanFunctionReturn(time.time(), col_hits, True)


    def _get_application(self, scan_function, persistence):
        def application(stdscr):
            curses.curs_set(0)
            stdscr.nodelay(1)
            # calculate the offset of the screen
            y_offset, x_offset = ChipViewer._get_offset(*stdscr.getmaxyx())
            stdscr.addstr(y_offset - 2, x_offset, "q to quit")
            stdscr.refresh()
            stay_in_loop = True
            while stay_in_loop:
                # run the scan
                scan_results = scan_function()
                self.event_history.append(scan_results)
                stay_in_loop = scan_results.keep_going
                # process the results
                for i, col_hit in enumerate(scan_results.column_hits):
                    col_diagram = np.zeros(64)
                    col_diagram[col_hit] = 1
                    if persistence:
                        col_diagram = np.logical_or(col_diagram,
                            self.persistence_history[i]).astype(int)
                        self.persistence_history[i] = col_diagram
                    # display the results
                    result_str = ChipViewer._present_array(col_diagram)
                    stdscr.addstr(i+y_offset, x_offset, result_str)
                stdscr.refresh()
                c = stdscr.getch()
                if c == ord('q'):
                    stay_in_loop = False
                if c == ord('x'):
                    self.persistence_history = np.zeros((18,64))
        return application

    def run_curses(self, scan_function=None, persistence=False):
        """
        Run the curses application with the given scanning function.

        The scan function should take no input and should output a
        2-tuple. The first item should be a list of lists, where each
        outer list is a column of the chip and each inner list lists the
        rows that have been hit. The second item should be a boolean
        which is True if the program should repeat, False if the program
        should stop running. It will be run in an infinite loop until
        the 2nd item of the tuple is False.
        """
        # Do this by default, if no function is specified
        if scan_function is None:
            self.scanner = None
            self._have_hardware = True
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
            if self._have_hardware:
                scan_function = ChipViewer._get_scan_results_hardware
                scan_function = functools.partial(scan_function, self.scanner)
            else:
                scan_function = ChipViewer._get_scan_results_software
                scan_function = functools.partial(scan_function, self.scanner)

        # Do this always
        curses.wrapper(self._get_application(scan_function, persistence))
        self._save_history()

if __name__ == "__main__":
    logging.basicConfig(filename="tuning.log", level=logging.DEBUG)
    app = ChipViewer()
    app.history_file = "history.txt"
    app.run_curses(persistence=True)
