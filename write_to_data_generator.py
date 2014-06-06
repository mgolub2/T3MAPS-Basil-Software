"""
Module for writing an arbitrary string of bits to the data generator.

"""

import visa

data_generator = visa.GpibInstrument("GPIB::3", board_number=0)

def set_pattern_bits(row_number, start_position, data_bits):
    """
    Write the given data bits to the data generator.

    data_bits should be a string containing 1's and 0's.
    """
    length = len(data_bits)
    length_of_length = len(str(length))
    args = {length:length, num_digits:length_of_length, row_number:row_number, start_position:start_position,
    data_bits:data_bits}
    command_string = "data:pattern:bit {row_number},{start_position},{length},#{num_digits}{length}{data_bits};"
    command_string.format(*args)

# set the memory size
data_generator.write("data:msize 64;")

# check the memory size
memsize = data_generator.ask("data:msize?;")
if(memsize == ":DATA:MSIZE 64"):
    print "memory size set"
else:
    print "memory size did not set:", memsize


# deletes all blocks; adds block "START" with size 64
data_generator.write("data:block:delete:all;") 
data_generator.write("data:block:rename \"UNNAMED\",\"START\";")
data_generator.write("data:block:size \"START\", 64;")

# sets the output pattern update method to manual
data_generator.write("mode:update manual;")

# sets the data memory bit pattern; position: 0, address: 0, length: 4, data: 0101; then prints the sequence
data_generator.write("data:pattern:bit 6,0,4,#141111;")
data_generator.write("data:update;")
print(data_generator.ask("data:pattern:bit? 6,0,4;"))
 
# sets the internal clock oscillator frequency to 100Mhz
data_generator.write("source:oscillator:internal:frequency 100MHZ;")
print(data_generator.ask("source:oscillator:internal:frequency?;"))
