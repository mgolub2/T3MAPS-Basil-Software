"""
Inject charge onto the chip and see if we can see it.

Injection is done using an external device, such as a function
generator.

"""
from lt3maps.lt3maps import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("column_number", type=int)
args = parser.parse_args()
column_number = args.column_number

chip = Pixel("lt3maps/lt3maps.yaml")

# set up the global dac register
chip.set_global_register(
        PrmpVbp=142,
        PrmpVbf=11,
        vth=150,
        DisVbn=49,
        VbpThStep=100,
        PrmpVbnFol=35,
        column_address=63
        )
chip.write_global_reg(load_DAC=True)

chip.set_global_register(
        column_address=column_number,
        config_mode=3)
chip.write_global_reg()

chip.set_pixel_register("0"*64)
chip.write_pixel_reg()

chip.set_global_register(
        column_address=column_number,
        LD_IN0_7=bitarray('11111111'),
        LDENABLE_SEL=1,
        )
chip.write_global_reg()

chip.set_global_register(
        column_address=column_number,
        LD_IN0_7=bitarray('00000000'),
        LDENABLE_SEL=1,
        )
chip.write_global_reg()

# run
chip.run_seq()
