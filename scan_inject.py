"""
Scanner module.

Read hit data off the chip.

Injection is done using an external device, such as a function
generator.

"""

from lt3maps.lt3maps import *
import numpy as np
import time

class Scanner(object):
    """
    Scan for hits on the LT3MAPS chip.

    """

    def __init__(self, config_file_location):
        self.chip = Pixel(config_file_location)
        self.hits = []

    def _set_bit_latches(self, column_number):
        """
        Set the hit and inject latches for the given column.

        """
        chip = self.chip

        # Construct the pixel register input
        PIXEL_REGISTER_LENGTH = len(chip['PIXEL_REG'])
        pixel_register_input = "1" * PIXEL_REGISTER_LENGTH

        chip.set_global_register(
            column_address=column_number)
        chip.write_global_reg()

        chip.set_pixel_register(pixel_register_input)
        chip.write_pixel_reg()

        # construct a dict of strobes to pass to set_global_register
        strobes = {'hit_strobe': 1, 'inject_strobe': 1}

        # Enable the strobes
        chip.set_global_register(
            column_address=column_number,
            enable_strobes=1,
            **strobes
            )
        chip.write_global_reg()

        # Disable the strobes. (New values are saved.)
        chip.set_global_register(
            column_address=column_number
            )
        chip.write_global_reg()
        return

    def _reset_hit_configuration(self, column_number):
        """
        Reset the S0 and HitLd configuration to "active" mode.

        """
        chip = self.chip
        # Reset configuration: Configure S0, and HitLD
        chip.set_global_register(
            column_address=column_number,
            config_mode=0,
            S0=1,
            S1=0,
            HITLD_IN=1,
            SRCLR_SEL=1
            )
        chip.write_global_reg()

        chip.set_global_register(
            column_address=column_number,
            S0=1,
            S1=0,
            HITLD_IN=1,
            )
        chip.write_global_reg()

        # run
        #chip.run(get_output=False)
        return

    def _read_column_hits(self, column_number):
        """
        Read the hits from the pixel shift register.

        """
        chip = self.chip

        # reset the S0 and HitLD to 0
        chip.set_global_register(column_address=column_number)
        chip.write_global_reg()

        # read out the pixel register
        chip.set_pixel_register("0" * 64)
        chip.write_pixel_reg()

        # get the (hit) output
        #output = chip.run()
        #return output

    def _set_latches_for_scan(self, column_number):
        """
        Initialize the latches to prepare for a scan.

        TODO: Currently enables hit and inject. Don't need inject
        for a true source scan...just for debugging.

        """
        chip = self.chip

        # initialize all latches to 0
        latches_to_strobe = ['hitor_strobe', 'hit_strobe', 'inject_strobe']
        self._set_bit_latches(column_number)

        # Enable the desired strobes: every other bit, for a recognizable pattern
        latches_to_strobe = ['hit_strobe', 'inject_strobe'] # TODO: change inject
        self._set_bit_latches(column_number)

        # Remove the bits from setting the strobes
        chip.set_pixel_register("0" * 64)
        chip.write_pixel_reg()

        chip.run(get_output=False)
        return

    def scan(self):
        """
        Perform a source scan and record all hits.

        """
        NUM_COLUMNS = 18
        # set up the global dac register
        self.chip.set_global_register(
            PrmpVbp=142,
            PrmpVbf=11,
            vth=150,
            DisVbn=49,
            VbpThStep=100,
            PrmpVbnFol=35,
            )
        self.chip.write_global_reg(load_DAC=True)

        self.chip.run(get_output=False)

        for i in range(NUM_COLUMNS):
            self._set_latches_for_scan(i)

        #self._reset_hit_configuration(0)
        #self._reset_hit_configuration(1)
        #self.chip.run()

        for i in range(NUM_COLUMNS):
            self._reset_hit_configuration(i)
            self.chip.run()
            self._read_column_hits(i)

            output = self.chip.run()
            hits = np.nonzero(output)[0]
        #for i in range(2):
            #hits = np.nonzero(output[i*64:(i+1)*64])[0]
            #hits = np.nonzero(output)[0]
            self.hits.append({
                "column": i,
                "num_hits": len(hits),
                "hit_rows": hits,
                "time": time.time()
            })

if __name__ == "__main__":
    scanner = Scanner("lt3maps/lt3maps.yaml")

    scanner.scan()
    print scanner.hits[0]["time"] - scanner.hits[-1]["time"]
    print scanner.hits[0]
    print scanner.hits[1]
    print scanner.hits[4]
    print scanner.hits[17]
