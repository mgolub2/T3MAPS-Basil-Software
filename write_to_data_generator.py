"""
Module for writing an arbitrary string of bits to the data generator.

"""

import visa
import time

data_generator = visa.GpibInstrument("GPIB::3", board_number=0)
last_write_time = time.time()
def set_pattern_bits(data_generator, pattern_number, start_position, data_bits):
    """
    Write the given data bits to the data generator.

    data_bits should be a string containing 1's and 0's.
    """
    length = len(data_bits)
    length_of_length = len(str(length))
    args = dict(length=length, num_digits=length_of_length, pattern_number=pattern_number, start_position=start_position,
    data_bits=data_bits)
    command_string_template = "data:pattern:bit {pattern_number},{start_position},{length},#{num_digits}{length}{data_bits};"
    command_string = command_string_template.format(**args)
    print "sending " + command_string
    data_generator.write(command_string)
    time.sleep(0.002*len(data_bits)/4.0)

def init_channel(data_generator, pattern_number, data_bits=None):
    """
    Re-sets the given row's pattern to the given pattern.

    If the pattern is < 64 bits long, the extra bits will be 0's.
    If no data_bits are given, simply resets the channels' pattern to 0's.

    """
    set_pattern_bits(data_generator, pattern_number, 0, "0"*64)
    if data_bits is not None:
        set_pattern_bits(data_generator, pattern_number, 0, data_bits)

def init_all_channels_slow(data_generator, data_dict, num_patterns=12):
    """
    Set all the channels according to the bitstring in data_dict[pattern_num].

    If a particular pattern number is not specified, reset it to 0's.

    """
    for pattern_num in range(num_patterns):
        bit_string = data_dict.get(pattern_num, None) # default to None if data_dict[pattern_num] does not exist
        init_channel(data_generator, pattern_num, bit_string)

data_dict = {0:"1"*64,2:"10"*32, 4:"0"*32+"1"*32, 6:"1"*32+"0"*32}
data_matrix = ["00001" for i in xrange(36)]

def init_all_channels(data_generator, start_address, data_matrix):
    """
    NOT COMPLETE: need to send data as "bytes", e.g. "#210\x00\x00\x00\x00E....."
    Sets all of the channels according to the bitstring in data_matrix[pattern_num].

    <start_address> is the "column" or bit number to start at (0 to 65535).
    data_matrix must be a 36-item list of strings of 1's and 0's.

    """
    command_string_template = "data:pattern:word {address},{length},{data};"
    args = {}
    args['address'] = start_address
    args['length'] = len(max(data_matrix, key=lambda bits:len(bits)))
    data_string = "#"
    num_bytes = args['length']*5
    num_digits_in_num_bytes = len(str(num_bytes))
    data_string += str(num_digits_in_num_bytes) + str(num_bytes)
    
    for i in range(args['length']):
        data_string += "0000"
        for pattern_num in reversed(range(len(data_matrix))): # should be range(36) always
            try:
                data_string += data_matrix[pattern_num][i]
            except IndexError:
                data_string += 0
    args['data'] = data_string
    command_string = command_string_template.format(**args)
    #print "command_string ="
    #print command_string
    #data_generator.write(command_string)

#init_all_channels_slow(data_generator, data_dict)
init_all_channels(data_generator, 0, data_matrix)
"""
init_channel(data_generator, 6, "0"*32+"1"*32)
init_channel(data_generator, 4, "01"*32)
init_channel(data_generator, 2)

# set the memory size
data_generator.write("data:msize 64;")

# check the memory size
memsize = data_generator.ask("data:msize?;")
if(memsize == ":DATA:MSIZE 64"):
    print "memory size set"
else:
    print "memory size did not set:", memsize
time.sleep(1)
data_generator.write(get_pattern_bits_command(6, 0, "0"*10))
time.sleep(1)
data_generator.write(get_pattern_bits_command(2, 0, "0"*10))
time.sleep(1)


# deletes all blocks; adds block "START" with size 64
data_generator.write("data:block:delete:all;") 
data_generator.write("data:block:rename \"UNNAMED\",\"START\";")
_command(6,0,"10"*32))
#last_write_time = time.time()
#data_generator.write("data:update;")
#print(data_generator.ask("data:pattern:bit? 6,0,10;"))


data_generator.write(init_channel(5,"101010101"))

# wait at least 0.002 seconds before writing again.
time_passed = time.time()-last_write_time
if(time_passed < 0.2):
    time.sleep(0.2-time_passed)

data_generator.write(get_pattern_bits_command(4,0,"0"*30+"0101"+"0"*30))
last_write_time = time.time()
data_generator.write("data:update;")
print(data_generator.ask("data:pattern:bit? 2,2,20;"))
"""
