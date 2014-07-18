import unittest
from lt3maps.lt3maps import *
import time

class TestPixel(unittest.TestCase):
    """
    Test the Pixel class in lt3maps.py.

    """
    def setUp(self):
        # initialize the chip
        self.chip = Pixel("lt3maps/lt3maps.yaml")

    def tearDown(self):
        del self.chip

    def _setUp_global_register(self):
        self.chip.set_global_register(
            PrmpVbf=253, # will be output as "10111111"
            LD_IN0_7=bitarray("11111101"), # will be output as "10111111"
            empty_pattern="00000000"
            )

    def test_set_global_register(self):
        chip = self.chip
        self._setUp_global_register()

        desired_pattern = bitarray("0"*176)
        desired_pattern[16:24] = True
        desired_pattern[17] = False
        desired_pattern[158:166] = True
        desired_pattern[159] = False

        self.assertEqual(len(desired_pattern), len(chip['GLOBAL_REG'][:]))
        self.assertEqual(desired_pattern, chip['GLOBAL_REG'][:])

    def test_write_global_reg(self):
        chip = self.chip
        self._setUp_global_register()
        chip.write_global_reg()

        desired_pattern_shift_in = bitarray("0"*178)
        desired_pattern_shift_in[16:24] = True
        desired_pattern_shift_in[22] = False
        desired_pattern_shift_in[158:166] = True
        desired_pattern_shift_in[164] = False

        self.assertEqual(len(desired_pattern_shift_in), len(chip._blocks[-1]['SHIFT_IN'][:]))
        self.assertEqual(desired_pattern_shift_in, chip._blocks[-1]['SHIFT_IN'][:])

    def test_write_global_reg_no_DAC(self):
        chip = self.chip
        self._setUp_global_register()
        chip.write_global_reg()
        print chip._blocks[-1]['GLOBAL_DAC_LD'][:]
        self.assertEqual(False, chip._blocks[-1]['GLOBAL_DAC_LD'][-1])

    def test_write_global_reg_yes_DAC(self):
        chip = self.chip
        self._setUp_global_register()
        chip.write_global_reg(load_DAC=True)
        print chip._blocks[-1]['GLOBAL_DAC_LD'][:]
        self.assertEqual(True, chip._blocks[-1]['GLOBAL_DAC_LD'][-1])

if __name__ == "__main__":
    unittest.main(buffer=True)
