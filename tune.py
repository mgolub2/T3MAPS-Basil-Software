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
        self.global_threshold = 80
        self.scanner = scan.Scanner("lt3maps/lt3maps.yaml")
        self.scanner.set_all_TDACs(0)
        self.viewer = None
        self.tuned_pixels = []
        self._noisy_pixels = []
        if view:
            self.viewer = scan_analysis.ChipViewer()

    def tune(self):
        if self.viewer is None:
            self._tune_loop()
        else:
            self.viewer.run_curses(self.get_scan_function(range(1,17)))

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

            Initialize all pixels' TDACs to 31.

            Repeat the following until either:

            * All pixels have been marked as tuned, or

            * At least one pixel's TDAC value is set to 0
            
              - Lower the TDAC values of all untuned pixels by 1.

              - For each untuned pixel which registers a hit:

                  - Increase its TDAC value by 1.

                  - Mark it as tuned.

        """
        num_pixels_to_tune = len(columns_to_scan) * self.scanner.chip.num_rows
        def scan_function():
            # initialize
            keep_going = True
            global_threshold = self.global_threshold
            self.scanner.reset()

            # Scan
            self.scanner.scan(3, 1, global_threshold)

            # find out which pixels were hit
            col_hits = self._get_column_hits_list(columns_to_scan)
            hit_pixels = self._get_hit_pixels(col_hits)
            logging.debug("number of hit pixels: " + str(len(hit_pixels)))

            # analyze results
            # first see if any hit pixels are "too noisy" and should be
            # ignored.
            at_least_one_real_hit = self._has_real_hits(col_hits)

            # Check if there were any hits
            if not at_least_one_real_hit:
                # Reset noise counts for previously-hit pixels
                for pixel in self._noisy_pixels:
                    del pixel.noise_count
                self._noisy_pixels = []
            else:
                # if there are hits, increase the TDACs of the hit pixels
                # raise those pixels' TDAC values
                num_maxed_out_pixels = 0
                for col, row in hit_pixels:
                    pixel = self.scanner.chip._pixels[col][row]
                    self._update_pixel(pixel)
                # Apply new TDAC values to chip
                self.scanner.chip._apply_pixel_TDAC_to_chip()
                #logging.debug("new TDAC array:")
                #logging.debug(self.scanner.chip.pixel_TDAC_matrix()[4])
                if num_maxed_out_pixels >= 50:
                    keep_going = False
            logging.info("number of pixels tuned: " +
                str(len(self.tuned_pixels)))
            if len(self.tuned_pixels) == num_pixels_to_tune:
                keep_going = False
            num_noisy_pixels = len([0 for pixel in self.tuned_pixels if
                                   hasattr(pixel, 'too_noisy')])
            if not at_least_one_real_hit or len(hit_pixels) - num_noisy_pixels < 10:
                self.global_threshold = global_threshold - 1
            if self.global_threshold < 0:
                keep_going = False
            return col_hits, keep_going
        return scan_function

    def _update_pixel(self, pixel):
        col, row = pixel.column, pixel.row
        old_value = pixel.TDAC
        if not hasattr(pixel, 'too_noisy') and old_value < 31:
            logging.debug(("(%i,%i) old_value = " % (col,row))+ str(old_value))
        # ensure that no TDAC gets bigger than 31
        if old_value == 31:
            num_maxed_out_pixels += 1
        else:
            pixel.TDAC = old_value + 1
            if not (pixel in self.tuned_pixels):
                self.tuned_pixels.append(pixel)
            if not (pixel in self._noisy_pixels):
                self._noisy_pixels.append(pixel)
                pixel.noise_count = 0
            pixel.noise_count += 1
            if pixel.noise_count == 4:
                pixel.too_noisy = True

    def _get_column_hits_list(self, columns_to_scan):
        col_hits = []
        for i in range(len(self.scanner.hits[0]['data'])):
            if i in columns_to_scan:
                col_hits.append(self.scanner.hits[0]['data'][i]['hit_rows'])
            else:
                 col_hits.append([])
        return col_hits

    def _has_real_hits(self, col_hits):
        at_least_one_real_hit = False
        for col_num, column in enumerate(col_hits):
            for row_num in column:
                pixel = self.scanner.chip._pixels[col_num][row_num]
                if not hasattr(pixel, 'too_noisy'):
                    at_least_one_real_hit = True
        return at_least_one_real_hit

if __name__ == "__main__":
    logging.basicConfig(filename="tuning.log", level=logging.DEBUG)
    tuner = Tuner(view=True)
    tuner.tune()
