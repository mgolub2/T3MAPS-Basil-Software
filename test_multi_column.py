"""
Test the ability of the lt3maps software to read and write to multiple columns.

"""
import unittest
from lt3maps.lt3maps import *

class TestColumns(unittest.TestCase):
    def setUp(self):
        # initialize the chip
        self.chip = T3MAPSChip("lt3maps/lt3maps.yaml")
        chip['GLOBAL_REG']['global_readout_enable'] = 0# size = 1 bit
        chip['GLOBAL_REG']['SRDO_load'] = 0# size = 1 bit
        chip['GLOBAL_REG']['NCout2'] = 0# size = 1 bit
        chip['GLOBAL_REG']['count_hits_not'] = 0# size = 1
        chip['GLOBAL_REG']['count_enable'] = 0# size = 1
        chip['GLOBAL_REG']['count_clear_not'] = 0# size = 1
        chip['GLOBAL_REG']['S0'] = 0# size = 1
        chip['GLOBAL_REG']['S1'] = 0# size = 1
        chip['GLOBAL_REG']['config_mode'] = 3# size = 2
        chip['GLOBAL_REG']['LD_IN0_7'] = 0# size = 8
        chip['GLOBAL_REG']['LDENABLE_SEL'] = 0# size = 1
        chip['GLOBAL_REG']['SRCLR_SEL'] = 0# size = 1
        chip['GLOBAL_REG']['HITLD_IN'] = 0# size = 1
        chip['GLOBAL_REG']['NCout21_25'] = 0# size = 5
        chip['GLOBAL_REG']['column_address'] = 0# size = 6
        chip['GLOBAL_REG']['DisVbn'] = 0# size = 8
        chip['GLOBAL_REG']['VbpThStep'] = 0# size = 8
        chip['GLOBAL_REG']['PrmpVbp'] = 0# size = 8
        chip['GLOBAL_REG']['PrmpVbnFol'] = 0# size = 8
        chip['GLOBAL_REG']['vth'] = 0# size = 8
        chip['GLOBAL_REG']['PrmpVbf'] = 0# size = 8

    def test_columns(self):
        chip = self.chip
        for i in range(16):
            chip.set_global_register(column_address=i)

            chip.set_pixel_register('1' + '0'*i + '1' + '0' * (64-i-2))

            chip.set_pixel_register('1'*(i+1) + '0'*(16-(i+1)) + '0'*48)

        output = chip.run()

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
