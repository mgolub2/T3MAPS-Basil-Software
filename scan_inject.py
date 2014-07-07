"""
Inject charge onto the chip and see if we can see it.

"""
from new_setup.lt3maps import *

chip = Pixel("new_setup/lt3maps.yaml")

# enable injection on a particular pixel (column 0, pixel 5, for example)

# select column 0
chip.set_global_register(column_address=0)
chip.write_global_reg()

# mark pixel 64 (in this case) to be enabled
chip.set_pixel_register('0'*63+ '1')
chip.write_pixel_reg()

# load the "enable" configuration
chip.set_global_register(
        column_address = 0,
        #S0=1,
        #HITLD_IN=1,
        LD_IN0_7=bitarray('00000110'),
        LDENABLE_SEL=1,
        PrmpVbp=142,
        PrmpVbf=11,
        vth=150,
        DisVbn=49,
        VbpThStep=100,
        PrmpVbnFol=35
        )

chip.write_global_reg(load_DAC=True)

print chip._blocks

# remove the "1" from the pixel shift register

# first select the column
chip.set_global_register(column_address = 0, LD_IN0_7=0)
chip.write_global_reg()

# then remove the 1
chip.set_pixel_register('0'*64)
chip.write_pixel_reg()

# set up injection pulse
chip.write_injection(20)

# get the output

chip.set_pixel_register('0' * 64)
chip.write_pixel_reg()

# run
chip.run_seq()

# output
output = chip.get_sr_output(invert=True)
for i in range(3):
    set_output = output[(64*i):(64*(i+1))]
    print "output", i
    print set_output
