"""
Inject charge onto the chip and see if we can see it.

Injection is done using an external device, such as a function
generator.

"""


def set_bit_latches(chip, column_address, rows, enable, *args):
    """
    Set the given 1-bit latches for the given pixels.

    All other pixels in the row have their corresponding latches
    disabled.

    `args` should be strings that correspond to the latches to be
    set. Acceptable values could be 'hit_strobe', 'inject_strobe',
    and 'hitor_strobe'. They may change, but they correspond to the
    appropriate name in the YAML file used to configure the chip.
    `enable` tells whether to set the latch to 0 or 1. It should be a
    boolean.

    For example,

    >>> set_latches(chip, 0, 63, True, 'hit_strobe', 'inject_strobe')

    will enable the hit and inject latches on the 0th row, 63rd pixel.
    All indexing starts from 0. (so 63rd pixel is "normal people"-64th)

    For multi-bit latches, e.g. TDAC, use the `set_latches` function,
    which lets you set arbitrary values to any set of latches.

    """
    # Make sure `rows` is a list (could be just a single number)
    if isinstance(rows, int):
        rows = [rows]

    # Construct the pixel register input (all 0's except for indices in "rows")
    PIXEL_REGISTER_LENGTH = len(chip['PIXEL_REG'])
    pixel_register_input = ""
    if enable:
        pixel_register_input =\
            [(i in rows) for i in range(PIXEL_REGISTER_LENGTH)]
        pixel_register_input = [str(int(b)) for b in pixel_register_input]
        pixel_register_input = "".join(pixel_register_input)[::-1]
    else:
        pixel_register_input = "0" * PIXEL_REGISTER_LENGTH

    # construct a dict of strobes to pass to set_global_register
    strobes = {arg: 1 for arg in args}

    chip.set_global_register(
        column_address=column_address)
    chip.write_global_reg()

    chip.set_pixel_register(pixel_register_input)
    chip.write_pixel_reg()

    # Enable the given strobes
    chip.set_global_register(
        column_address=column_address,
        enable_strobes=1,
        #TDAC_strobes=31,
        **strobes
        )
    chip.write_global_reg()

    # Disable the given strobes. (New values are saved.)
    chip.set_global_register(
        column_address=column_address,
        )
    chip.write_global_reg()
    return

if __name__ == "__main__":
    from lt3maps.lt3maps import *
    import argparse

    # parse command line input
    parser = argparse.ArgumentParser()
    parser.add_argument("column_number", type=int)
    parser.add_argument("s0", type=int)
    parser.add_argument("s1", type=int)
    parser.add_argument("hitld", type=int)

    parser.add_argument("--hit", action="store_true",
                        help="enable hit")
    parser.add_argument("--inject", action="store_true",
                        help="enable inject")
    parser.add_argument("--hitor", action="store_true",
                        help="enable hitor")
    args = parser.parse_args()
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

    # initialize all latches to 0
    latches_to_strobe = ['hitor_strobe', 'hit_strobe', 'inject_strobe']
    set_bit_latches(chip, args.column_number, range(64), False, *latches_to_strobe)

    # Enable the desired strobes
    latches_to_strobe = [key for key, value in strobes.iteritems() if value]
    set_bit_latches(chip, args.column_number, 63, True,
                    *latches_to_strobe)

    # Remove the bits from setting the strobes
    chip.set_pixel_register("01" * 32)
    chip.write_pixel_reg()

    # Configure S0, and HitLD
    chip.set_global_register(
        column_address=args.column_number,
        S0=args.s0,
        S1=args.s1,
        HITLD_IN=args.hitld
        )
    chip.write_global_reg()

    # run
    chip.run_seq()

    # capture the output from earlier shift registers
    extra_output = chip.get_sr_output(invert=True)
    print "first_output:"
    print extra_output

    # wait a little while for injection
    time.sleep(0.5)

    # reset the sequence to start again
    chip.reset_seq()

    # reset the S0 and HitLD to 0
    chip.set_global_register(column_address=args.column_number)
    chip.write_global_reg()

    # read out the pixel register
    chip.set_pixel_register("0" * 64)
    chip.write_pixel_reg()

    chip.run_seq()
    output = chip.get_sr_output(invert=True)
    print "output:"
    print output
