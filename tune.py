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
    def __init__(self, view=True):
        self.global_threshold = 255
        self.TDACs = [[0 for _ in range(64)] for _ in range(18)]
        if view:
            self.viewer = scan_analysis.ChipViewer()
            if not self.viewer._have_hardware:
                raise NotImplementedError("Need hardware connection.")

    def tune(self):
        viewer = getattr(self, 'viewer', None)
        if viewer is None:
            self._tune_loop()
        else:
            self.viewer.run_curses(self.get_scan_function())

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
        def scan_function(scanner):
            col_hits = []
            global_threshold = self.global_threshold
            scanner.reset()
            scanner.scan(1, 1, global_threshold)
            # make a matrix of pixel hits
            for i in range(len(scanner.hits[0]['data'])):
                col_hits.append(scanner.hits[0]['data'][i]['hit_rows'])
            # analyze results
            if sum(sum(col) for col in col_hits) == 0:
                # if no hits, reduce global threshold
                self.global_threshold = global_threshold - 5   
            else:
                # find the pixels which have been hit
                hit_pixels = [(col, row) for col, column in enumerate(col_hits)
                              for row, val in enumerate(column)
                              if val == 1]
                # raise those pixels' TDAC values
                for col, row in hit_pixels:
                    self.TDACs[col][row] += 1
                # TODO: Apply new TDAC values to chip
            return col_hits
        return scan_function

if __name__ == "__main__":
    tuner = Tuner()
    tuner.tune()
