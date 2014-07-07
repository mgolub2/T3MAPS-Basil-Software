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
        LD_IN0_7=bitarray('00000000'),
        LDENABLE_SEL=0,
        PrmpVbp=24,
        PrmpVbf=64,
        vth=255,
        DisVbn=255,
        VbpThStep=100,
        PrmpVbnFol=34
        )

chip.write_global_reg(load_DAC=True)

print chip._blocks

# remove the "1" from the pixel shift register

# first select the column
chip.set_global_register(column_address = 0)
chip.write_global_reg()

# then remove the 1
chip.set_pixel_register('0'*64)
chip.write_pixel_reg()


# run
chip.run_seq()

# output
output = chip.get_sr_output(invert=True)
for i in range(2):
    set_output = output[(64*i):(64*(i+1))]
    print "output", i
    print set_output

time.sleep(2)
chip.reset_seq()

# set up injection pulse
chip.write_injection(400)
chip.write_injection(400)
chip.write_injection(400)
chip.write_injection(400)
chip.write_injection(400)
chip.write_injection(400)

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
