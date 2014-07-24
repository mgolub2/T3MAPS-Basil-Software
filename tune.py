"""
A module for tuning the T3MAPS chip.

"""

import scan_inject as scan
import scan_analysis
import lt3maps
import logging

class Tuner(object):
    """
    Manages a chip tuning.

    """
    def __init__(self, view=True):
        self.global_threshold = 135
        self.scanner = scan.Scanner("lt3maps/lt3maps.yaml")
        self.viewer = None
        if view:
            self.viewer = scan_analysis.ChipViewer()

    def tune(self):
        if self.viewer is None:
            self._tune_loop()
        else:
            self.viewer.run_curses(self.get_scan_function())

    def _tune_loop(self):
        keep_going = True
        while keep_going:
            col_hits, keep_going = self.get_scan_function()()
            hit_pixels = self._get_hit_pixels(col_hits)
            print "(", self.global_threshold, ",", len(hit_pixels), ")"

    @staticmethod
    def _get_hit_pixels(col_hits):
        hit_pixels = [(col, row) for col, column in enumerate(col_hits)
                              for row in column]
        return hit_pixels

    def get_scan_function(self):
        """
        Tune the chip so all pixels have the same actual threshold.

        The following information is enough to recreate the result of a tuning:
        
        - The value of the global threshold.

        - The TDAC value for each pixel.

        Algorithm:

            Initialize global threshold to highest possible, so that no
            pixels fire. Initialize pixel TDACs to lowest possible, so that
            if a pixel fires, the TDAC can be raised and the pixel will no
            longer fire.

            Repeat the following until either:
            * All pixels' TDACs have been adjusted at least once, or

            * 5 pixels have reached their maximum TDACS. Then all
              as-yet-untriggered pixels are untuned.
            
              - Lower the global threshold until one pixel is hit due to
                noise.

              - Increase hit pixels' TDAC values until they are no longer
                triggered by noise.

        """
        def scan_function():
            logging.info("beginning scan_function")
            keep_going = True
            col_hits = []
            global_threshold = self.global_threshold
            self.scanner.reset()
            self.scanner.scan(1, 1, global_threshold)
            # make a matrix of pixel hits
            for i in range(len(self.scanner.hits[0]['data'])):
                col_hits.append(self.scanner.hits[0]['data'][i]['hit_rows'])
            # analyze results
            #self.global_threshold = global_threshold - 5   # TODO
            if sum(sum(col) for col in col_hits) == 0:
                # if no hits, reduce global threshold
                self.global_threshold = global_threshold - 1
                if self.global_threshold < 0:
                    keep_going = False
            else:
                # find the pixels which have been hit
                hit_pixels = self._get_hit_pixels(col_hits)
                # raise those pixels' TDAC values
                for col, row in hit_pixels:
                    old_value = self.scanner.chip._pixels[col][row].TDAC
                    if old_value + 2 > 31:
                        old_value -= 2
                    logging.debug(("(%i,%i) old_value = " % (col,row))+ str(old_value))
                    self.scanner.chip._pixels[col][row].TDAC = old_value + 2
                # Apply new TDAC values to chip
                self.scanner.chip._apply_pixel_TDAC_to_chip()
                logging.debug("new TDAC array:")
                logging.debug(self.scanner.chip.pixel_TDAC_matrix()[0])
            return col_hits, keep_going
        return scan_function

if __name__ == "__main__":
    logging.basicConfig(filename="tuning.log", level=logging.DEBUG)
    tuner = Tuner(view=False)
    tuner.tune()
