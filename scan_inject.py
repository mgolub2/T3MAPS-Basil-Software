"""
Scanner module.

Read hit data off the chip.

Injection is done using an external device, such as a function
generator.

"""

from lt3maps.lt3maps import *
import numpy as np
import time
import yaml
import argparse

import logging
class Scanner(object):
    """
    Scan for hits on the LT3MAPS chip.

    """

    def __init__(self, config_file_location):
        self.chip = T3MAPSChip(config_file_location)
        self.hits = []
        self._outputs = []

    def _reset_hit_configuration(self, column_number):
        """
        Reset the S0 and HitLd configuration to "active" mode.

        """
        chip = self.chip
        # Reset configuration: Configure S0, and HitLD
        chip.set_global_register(
            column_address=column_number,
            config_mode=3,
            S0=1,
            S1=0,
            HITLD_IN=1,
            SRCLR_SEL=1
            )

        chip.set_global_register(
            column_address=column_number,
            config_mode=3,
            S0=1,
            S1=0,
            HITLD_IN=1,
            )

        return

    def _read_column_hits(self, column_number_start, column_number_stop):
        """
        Read the hits from the pixel shift register.

        Adopts the `range` convention of running from [start, stop),
        excluding stop.

        """
        chip = self.chip

        for column_number in range(column_number_start, column_number_stop):
            # reset the S0 and HitLD to 0
            chip.set_global_register(column_address=column_number)

            # read out the pixel register
            chip.set_pixel_register("0" * chip.num_rows)

    def _set_latches_for_scan(self, column_number):
        """
        Initialize the latches to prepare for a scan.

        TODO: Currently enables hit and inject. Don't need inject
        for a true source scan...just for debugging.

        """
        chip = self.chip

        # initialize all latches to 0
        latches_to_strobe = ['hitor_strobe', 'hit_strobe', 'inject_strobe',
                             'TDAC_strobes', 31]
        chip.set_bit_latches(column_number, [], *latches_to_strobe)

        # Enable the desired strobes: every other bit, for a recognizable pattern
        latches_to_strobe = ['hit_strobe', 'inject_strobe'] # TODO: change inject
        chip.set_bit_latches(column_number, None, *latches_to_strobe)

        # Remove the bits from setting the strobes
        chip.set_pixel_register("0" * chip.num_rows)

        chip.run(get_output=False)
        return

    def reset(self):
        """
        Reset the scanner to prepare to take a new scan.

        """
        self.hits = []
        self._outputs = []

    def scan(self, sleep, cycles, global_threshold=150):
        """
        Perform a source scan and record all hits.

        """
        NUM_COLUMNS = self.chip.num_columns
        NUM_ROWS = self.chip.num_rows
        # set up the global dac register
        logging.debug("global threshold = " + str(global_threshold))
        self.chip.set_global_register(
            PrmpVbp=142,
            PrmpVbf=11,
            vth=global_threshold,
            DisVbn=49,
            VbpThStep=100,
            PrmpVbnFol=35,
            load_DAC=True
        )

        self.chip.run(get_output=False)

        for i in range(NUM_COLUMNS):
            self._set_latches_for_scan(i)

        num_cols_together = 9
        for _ in range(cycles):
            self._reset_hit_configuration(0)
            self.chip.run()
            time.sleep(sleep)
            for i in range(0, NUM_COLUMNS, num_cols_together):
                self._read_column_hits(i, i + num_cols_together)
                output = self.chip.run()
                read_time = time.time()
                starts = range(0, num_cols_together * NUM_ROWS, NUM_ROWS)
                outputs = [(output[i:i+NUM_ROWS], read_time) for i in starts]
                self._outputs.extend(outputs)

        cycle_num = 0
        for i, (output, read_time) in enumerate(self._outputs):
            if i % NUM_COLUMNS == 0:
                cycle_num = i/NUM_COLUMNS
                self.hits.append({'cycle': cycle_num, 'data': []})
            hits = np.nonzero(output)[0]
            self.hits[cycle_num]['data'].append({
                "column": i % NUM_COLUMNS,
                "num_hits": len(hits),
                "hit_rows": hits.tolist(),
                "time": read_time
            })

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sleep", type=float, default=0)
    parser.add_argument("--cycles", type=int, default=1)
    args = parser.parse_args()
    scanner = Scanner("lt3maps/lt3maps.yaml")

    scanner.scan(args.sleep, args.cycles)
    print "time: ", scanner.hits[-1]['data'][-1]["time"] -\
        scanner.hits[0]['data'][0]["time"]
    outfile = open("out.yaml", "w")
    outfile.write(yaml.dump(scanner.hits))
