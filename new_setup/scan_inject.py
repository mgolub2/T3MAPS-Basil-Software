"""
Inject charge onto the chip and see if we can see it.

Injection is done using an external device, such as a function
generator.

"""
from lt3maps.lt3maps import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("column_number", type=int)
enable_grp = parser.add_mutually_exclusive_group()
enable_grp.add_argument("--enable", action="store_true", help="strobes to 1")
# this argument is ignored. it's just a good placeholder for "not --enable"
enable_grp.add_argument("--disable", action="store_true", help="strobes to 0")
parser.add_argument("--hit", action="store_true", help="transparent hit")
parser.add_argument("--inject", action="store_true",
                    help="transparent inject")
parser.add_argument("--hitor", action="store_true",
                    help="transparent hitor")
args = parser.parse_args()
column_number = args.column_number
args.enable = str(int(args.enable))
strobes = {
    "hit_strobe": int(args.hit),
    "inject_strobe": int(args.inject),
    "hitor_strobe": int(args.hitor)
}

chip = Pixel("lt3maps/lt3maps.yaml")

# set up the global dac register
chip.set_global_register(
        PrmpVbp=142,
        PrmpVbf=11,
        vth=150,
        DisVbn=49,
        VbpThStep=100,
        PrmpVbnFol=35,
        )
chip.write_global_reg(load_DAC=True)

chip.set_global_register(
        column_address=column_number)
chip.write_global_reg()

chip.set_pixel_register(args.enable + "0" * 63)
chip.write_pixel_reg()

chip.set_global_register(
        column_address=column_number,
        enable_strobes=1,
        **strobes
        )
chip.write_global_reg()

chip.set_global_register(
        column_address=column_number,
        )
chip.write_global_reg()

# run
chip.run_seq()
