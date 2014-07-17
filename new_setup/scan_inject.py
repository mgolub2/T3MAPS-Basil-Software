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
        pixel_register_input = [(i in rows) for i in range(PIXEL_REGISTER_LENGTH)]
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
            column_address=column_number,
            enable_strobes=1,
            **strobes
            )
    chip.write_global_reg()

    # Disable the given strobes. (New values are saved.)
    chip.set_global_register(
            column_address=column_number,
            )
    chip.write_global_reg()
    return



if __name__ == "__main__":
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
    #args.enable = str(int(args.enable))
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

    latches_to_strobe = [key for key, value in strobes.iteritems() if value ]
    set_bit_latches(chip, column_number, 63, args.enable, *latches_to_strobe)

    # run
    chip.run_seq()
