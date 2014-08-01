"""
A module for tuning the T3MAPS chip.

"""

import scan_inject as scan
import scan_analysis
import lt3maps
import logging
import struct
import time

class Tuner(object):
    """
    Manages a chip tuning.

    """
    def __init__(self, view=True):
        self.global_threshold = 60
        self.scanner = scan.Scanner("lt3maps/lt3maps.yaml")
        self.scanner.set_all_TDACs(0)
        self.viewer = None
        if view:
            self.viewer = scan_analysis.ChipViewer()

    def tune(self):
        # Initialize all TDAC values to 31
        self.scanner.set_all_TDACs(24)

        # Mark all pixels as untuned
        self.untuned_pixels = [pixel for column in self.scanner.chip._pixels
                               for pixel in column]
        self.num_pixels_total = len(self.untuned_pixels)
        self.tuned_pixels = []
        self.iteration = 1
        self.num_iterations = 4

        if self.viewer is None:
            self._tune_loop()
        else:
            self.viewer.run_curses(self.get_scan_function(range(1,17)))
        self.scanner.chip.save_TDAC_to_file("tune_results.yaml")

    def _tune_loop(self):
        keep_going = True
        while keep_going:
            col_hits, keep_going = self.get_scan_function(range(1,17))()
            hit_pixels = self._get_hit_pixels(col_hits)
            print "(", self.global_threshold, ",", len(hit_pixels), ")"

    @staticmethod
    def _get_hit_pixels(col_hits):
        hit_pixels = [(col, row) for col, column in enumerate(col_hits)
                              for row in column]
        return hit_pixels

    def get_scan_function(self, columns_to_scan=range(18)):
        """
        Tune the chip so all pixels have the same actual threshold.

        The following information is enough to recreate the result of a tuning:
        
        - The value of the global threshold.

        - The value of the TDAC step size.

        - The TDAC value for each pixel.

        Algorithm:

            Initialize the global threshold and TDAC step size so the following
            hold:

            * If all pixels' TDACs are 0, then all (or almost all)
            pixels fire.

            * If all pixels' TDACs are 31, then none (or almost none) of
            the pixels fire.

            Initialize all pixels' TDACs to 31. Mark all pixels as
            untuned.

            Repeat the following until either:

            * All pixels have been marked as tuned, or

            * At least one pixel's TDAC value is set to 0

              - Scan.

              - For each untuned pixel:
              
                  - If it registers a hit:

                      - Increase its TDAC value by 1.

                      - Mark it as tuned.

                  - If not:
                      - Lower its TDAC value by 1.


        """
        def scan_function():
            # initialize
            keep_going = True
            self.scanner.reset()

            logging.info("number of pixels left to tune: %i",
            len(self.untuned_pixels))
            # Scan
            self.scanner.scan(2, 1, self.global_threshold)

            # find out which pixels were hit
            col_hits = self._get_column_hits_list(columns_to_scan)
            hit_pixels = self._get_hit_pixels(col_hits)
            logging.debug("number of hit pixels: " + str(len(hit_pixels)))

            if self.iteration == 1:
                self.hit_count = {}
            for pixel_address in hit_pixels:
                prev_hit_count = self.hit_count.get(pixel_address, 0)
                self.hit_count[pixel_address] = prev_hit_count + 1
            if self.iteration < self.num_iterations:
                self.iteration += 1
                return col_hits, True
            else:
                self.iteration = 1

            # analyze results
            for pixel in self.untuned_pixels[:]:
                if (self.hit_count.get((pixel.column, pixel.row),0) >
                    self.num_iterations/2.0):
                    try:
                        for _ in range(5):
                            pixel.TDAC += 1
                        if (pixel.column, pixel.row) == (1, 58):
                            logging.debug(str(pixel))
                    # Handle case where pixel is hit even at maximum TDAC.
                    except ValueError as e:
                        if "too big to fit into" in str(e):
                            pass
                        else:
                            raise
                    self.untuned_pixels.remove(pixel)
                    logging.debug("marking pixel as tuned: (%i,%i)",
                                  pixel.column,pixel.row)
                else:
                    if pixel.TDAC == 0:
                        keep_going = False
                    else:
                        pixel.TDAC -= 1

            self.scanner.chip._apply_pixel_TDAC_to_chip()
            if len(self.untuned_pixels) == 0:
                keep_going = False

            logging.debug(self.scanner.chip.pixel_TDAC_matrix()[1][:10])
            if len(hit_pixels) > self.num_pixels_total/2:
                wait = 5
                logging.info("waiting %is to calm down", wait)
                time.sleep(wait)
            return scan_analysis.ScanFunctionReturn(time.time(), col_hits,
                keep_going)
        return scan_function

    def _get_column_hits_list(self, columns_to_scan):
        col_hits = []
        for i in range(len(self.scanner.hits[0]['data'])):
            if i in columns_to_scan:
                col_hits.append(self.scanner.hits[0]['data'][i]['hit_rows'])
            else:
                 col_hits.append([])
        return col_hits

if __name__ == "__main__":
    logging.basicConfig(filename="tuning.log", level=logging.DEBUG)
    tuner = Tuner(view=True)
    tuner.tune()
