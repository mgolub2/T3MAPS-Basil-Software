"""
A module for tuning the T3MAPS chip.

"""

import scan_inject as scan
import scan_analysis
import lt3maps

class Tuner(object):
    """
    Manages a chip tuning.

    """
    def __init__(self):
        if not scan_analysis.have_hardware:
            raise NotImplementedError("Don't know what to do when there's no \
            hardware")

    def tune(self):
        scan_analysis.run_curses(Tuner.scan_function)

    @staticmethod
    def scan_function(scanner):
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
        col_hits = []
        global_threshold = 255
        scanner.reset()
        scanner.scan(1, 1, global_threshold)
        # make a matrix of pixel hits
        for i in range(len(scanner.hits[0]['data'])):
            col_hits.append(scanner.hits[0]['data'][i]['hit_rows'])
        return col_hits

if __name__ == "__main__":
    tuner = Tuner()
    tuner.tune()
