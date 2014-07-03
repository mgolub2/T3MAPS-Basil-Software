"""
Test the ability of the lt3maps software to read and write to multiple columns.

"""
import argparse
from new_setup.lt3maps import *


def test_columns(min_col, max_col):
    # initialize the chip
    chip = Pixel("new_setup/lt3maps.yaml")

    for i in range(min_col,max_col+1):
        chip.set_global_register(column_address=i)

        chip.write_global_reg()

        chip.set_pixel_register('1' + '0'*i + '1' + '0' * (64-i-2))

        chip.write_pixel_reg()

        chip.set_pixel_register('1000'*16)

        chip.write_pixel_reg()

    chip.run_seq()

    output = chip.get_sr_output(invert=True)

    for i in range(min_col, max_col + 1):
        j = i-min_col
        column_output = output[(128*j):(128*(j+1))]
        print "column", i
        print column_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("min_col", help="the low column number to test", type=int)
    parser.add_argument("max_col", help="the high column number to test", type=int)
    args = parser.parse_args()
    test_columns(args.min_col, args.max_col)
