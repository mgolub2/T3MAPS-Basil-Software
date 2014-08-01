"""
A module for tuning the T3MAPS chip.

"""

import scan_inject as scan
import scan_analysis
import lt3maps
import logging
import struct

class Tuner(object):
    """
    Manages a chip tuning.

    """
    def __init__(self, view=True):
        self.global_threshold = 68
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
        self.tuned_pixels = []

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

            # Scan
            self.scanner.scan(10, 1, self.global_threshold)

            # find out which pixels were hit
            col_hits = self._get_column_hits_list(columns_to_scan)
            hit_pixels = self._get_hit_pixels(col_hits)
            logging.debug("number of hit pixels: " + str(len(hit_pixels)))

            tuned_hits = [p for p in self.tuned_pixels if (p.column, p.row) in
                hit_pixels]
            try_again = len(tuned_hits) > 10

            # analyze results
            pixels_to_adjust = self.untuned_pixels
            if try_again:
                pixels_to_adjust = self.tuned_pixels
                for pixel in self.tuned_pixels:
                    logging.debug("tuned pixel: (%i,%i), TDAC = %i",
                                  pixel.column,pixel.row, pixel.TDAC)
            for pixel in pixels_to_adjust:
                if (pixel.column, pixel.row) in hit_pixels:
                    try:
                        for _ in range(5):
                            pixel.TDAC += 1
                    # Handle case where pixel is hit even at maximum TDAC.
                    except ValueError as e:
                        if "too big to fit into" in str(e):
                            pass
                        else:
                            raise
                    if not try_again:
                        self.untuned_pixels.remove(pixel)
                        self.tuned_pixels.append(pixel)
                        logging.debug("marking pixel as tuned: (%i,%i)",
                                      pixel.column,pixel.row)
                elif not try_again:
                    if pixel.TDAC == 0:
                        keep_going = False
                    elif len(hit_pixels) < 20:
                        pixel.TDAC -= 1
                    else:
                        pass

            self.scanner.chip._apply_pixel_TDAC_to_chip()
            if len(self.untuned_pixels) == 0:
                keep_going = False

            logging.debug(self.scanner.chip.pixel_TDAC_matrix()[1][:10])
            return col_hits, keep_going
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
