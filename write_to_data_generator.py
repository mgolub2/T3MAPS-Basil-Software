"""
Module for writing an arbitrary string of bits to the data generator.

"""

import visa

data_generator = visa.GpibInstrument("GPIB::3", board_number=0)
def write(data_generator, command):
    data_generator.write(command+"\n")

# reset data generator
#data_generator.write("*RST")

# ask for all data info
#print(data_generator.ask("DATA?"))

# set the memory size to 1024
write(data_generator,"DATA:MSIZe 1024")

# check the memory size
memsize = data_generator.ask("DATA:MSIZe?")
if(memsize == ":DATA:MSIZE 1024"):
    print "memory size set"
else:
    print "memory size did not set:", memsize

# deletes all blocks; adds block "STARTBLOCK" with size 4
write(data_generator, "DATA:BLOCk:DELete:ALL") 
write(data_generator, "DATA:BLOCk:RENAME \"UNNAMED\",\"STARTBLOCK\"")
write(data_generator, "DATA:BLOCk:SIZE \"STARTBLOCK\", 4")

# sets the output pattern update method to manual
write(data_generator,"MODE:UPDATE MAN")

# sets the data memory bit pattern; position: 0, address: 0, length: 4, data: 0101; then prints the sequence
write(data_generator,"DATA:PATTERN:BIT 6,0,4,#140101")
data_generator.write("DATA:UPDATE")
print(data_generator.ask("DATA:PATTERN:BIT? 6,0,4"))
 
# sets the internal clock oscillator frequency to 100Mhz
write(data_generator,":SOURCE:OSCILLATOR:INTERNAL:FREQUENCY 100MHZ")
print(data_generator.ask(":SOURCE:OSCILLATOR:INTERNAL:FREQUENCY?"))
