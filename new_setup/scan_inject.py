"""
Inject charge onto the chip and see if we can see it.

"""
from lt3maps.lt3maps import *

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

# enable injection on a particular pixel

# select column 0
column_number = 0
chip.set_global_register(column_address=column_number)
chip.write_global_reg()

# mark pixel 64 (in this case) to be enabled
chip.set_pixel_register('0'*63 + '1')
chip.write_pixel_reg()

# load the "enable" configuration by letting the
# latches become transparent
chip.set_global_register(
        column_address=column_number,
        LD_IN0_7=bitarray('00000110'),
        LDENABLE_SEL=1,
        )
chip.write_global_reg()

# un-transparentify the latches
chip.set_global_register(
        column_address=column_number,
        #S0=1,
        #HITLD_IN=1
        )
chip.write_global_reg()

# remove the "1" from the pixel shift register
#chip.set_pixel_register('0'*64)
#chip.write_pixel_reg()

# run
chip.run_seq()

# output
output = chip.get_sr_output(invert=True)
for i in range(2):
    set_output = output[(64*i):(64*(i+1))]
    print "output", i
    print set_output

"""
time.sleep(0.02)
chip.reset_seq()

# set up injection pulse
for i in range(3):
    chip.write_injection(400)

chip.set_global_register(column_address=column_number)
chip.write_global_reg()

# get the output
chip.set_pixel_register('0' * 64)
chip.write_pixel_reg()

chip.run_seq()

# output
output = chip.get_sr_output(invert=True)
for i in range(2,3):
    set_output = output[(64*(i-2)):(64*(i-1))]
    print "output", i
    print set_output
"""
