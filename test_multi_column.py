"""
Test the ability of the lt3maps software to read and write to multiple columns.

"""
import unittest
from lt3maps.lt3maps import *

class TestColumns(unittest.TestCase):
    def setUp(self):
        # initialize the chip
        self.chip = Pixel("lt3maps/lt3maps.yaml")

    def test_columns(self):
        chip = self.chip
        for i in range(16):
            chip.set_global_register(column_address=i)

            chip.write_global_reg()

            chip.set_pixel_register('1' + '0'*i + '1' + '0' * (64-i-2))

            chip.write_pixel_reg()

            chip.set_pixel_register('1'*(i+1) + '0'*(16-(i+1)) + '0'*48)

            chip.write_pixel_reg()

        chip.run_seq()

        output = chip.get_sr_output(invert=True)

        for i in range(16):
            print "column", i
            column_output = output[(128*i):(128*(i+1))]
            print column_output
            desired_output = [0]*64 + [1] + [0]*i + [1] + [0]*(64-i-2)
            self.assertTrue(all(column_output[64:] == desired_output[64:]))


if __name__ == "__main__":
    # Run the test
    # 'buffer = True' causes prints to only go through if test fails.
    unittest.main(buffer=True)
