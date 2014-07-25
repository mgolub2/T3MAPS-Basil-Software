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
        num_pixels_to_tune = len(columns_to_scan) * self.scanner.chip.num_rows
        def scan_function():
            # initialize
            keep_going = True
            col_hits = []
            global_threshold = self.global_threshold
            self.scanner.reset()

            # Scan
            self.scanner.scan(3, 1, global_threshold)

            # make a matrix of pixel hits
            for i in range(len(self.scanner.hits[0]['data'])):
                if i in columns_to_scan:
                    col_hits.append(self.scanner.hits[0]['data'][i]['hit_rows'])
                else:
                     col_hits.append([])

            # analyze results
            # first see if any hit pixels are "too noisy" and should be
            # ignored.
            at_least_one_real_hit = False
            for col_num, column in enumerate(col_hits):
                for row_num in column:
                    pixel = self.scanner.chip._pixels[col_num][row_num]
                    if not hasattr(pixel, 'too_noisy'):
                        at_least_one_real_hit = True

            # Check if there were any hits
            if not at_least_one_real_hit:
                # if no hits, reduce global threshold
                self.global_threshold = global_threshold - 1
                if self.global_threshold < 0:
                    keep_going = False
                hit_pixels = self._get_hit_pixels(col_hits)
                logging.debug("number of hit pixels: " + str(len(hit_pixels)))
                # Reset noise counts for previously-hit pixels
                for pixel in self._noisy_pixels:
                    del pixel.noise_count
                self._noisy_pixels = []
            else:
                # if there are hits, increase the TDACs of the hit pixels
                # find the pixels which have been hit
                hit_pixels = self._get_hit_pixels(col_hits)
                # raise those pixels' TDAC values
                num_maxed_out_pixels = 0
                for col, row in hit_pixels:
                    pixel = self.scanner.chip._pixels[col][row]
                    old_value = pixel.TDAC
                    if not hasattr(pixel, 'too_noisy') and old_value < 31:
                        logging.debug(("(%i,%i) old_value = " % (col,row))+ str(old_value))
                    # ensure that no TDAC gets bigger than 31
                    if old_value == 31:
                        num_maxed_out_pixels += 1
                    else:
                        pixel = self.scanner.chip._pixels[col][row]
                        pixel.TDAC = old_value + 1
                        if not (pixel in self.tuned_pixels):
                            self.tuned_pixels.append(pixel)
                        if not (pixel in self._noisy_pixels):
                            self._noisy_pixels.append(pixel)
                            pixel.noise_count = 0
                        pixel.noise_count += 1
                        if pixel.noise_count == 4:
                            pixel.too_noisy = True
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
            return col_hits, keep_going
        return scan_function

if __name__ == "__main__":
    logging.basicConfig(filename="tuning.log", level=logging.DEBUG)
    tuner = Tuner(view=True)
    tuner.tune()
