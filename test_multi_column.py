"""
Test the ability of the lt3maps software to read and write to multiple columns.

"""
from new_setup.lt3maps import *

# initialize the chip
chip = Pixel("new_setup/lt3maps.yaml")

# Read from 2 different columns
chip.set_global_register(column_address=1)

chip.write_global_reg()

chip.set_pixel_register('1000'*16)

chip.write_pixel_reg()

chip.set_global_register(column_address=10)

chip.write_global_reg()

print chip._blocks

chip.set_pixel_register('10'*32)

chip.write_pixel_reg()


chip.run_seq()

output = chip.get_sr_output(invert=True)

print output
