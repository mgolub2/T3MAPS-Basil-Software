"""
Module for writing an arbitrary string of bits to the data generator.

"""

import visa
import time

class DataGenerator(visa.GpibInstrument):
    """
    Facilitates communication with a DG2020A data generator.

    """

    number_of_channels = 36

    def __init__(self, port=3):
        """
        Create a new DataGenerator using the given port.
 
        """
        visa.GpibInstrument.__init__(self, "GPIB::{port}".format(port=port), board_number=0)

        self.last_write_time = time.time()
        self.wait_time = 0

    @staticmethod
    def clock(num_clocks, num_cycles_per_clock, start_on_low=True):
        """
        Get a representation of a clock to go into the data generator.

        num_clocks is the number of high/low patterns to repeat.

        num_cycles_per_clock is the number of data generator cycles that
        fits in one high (or one low), i.e. half a clock length.
 
        if start_on_low, then the clock will start on low and end on high.

        """
        low = "0" * num_cycles_per_clock
        high = "1" * num_cycles_per_clock
        cycle = low + high if start_on_low else high + low
        return cycle * num_clocks

    @staticmethod
    def blank(num_cycles):
        """
        Get a blank data matrix to go into the init_all_channels method.

        """
        return ["0"*num_cycles] * DataGenerator.number_of_channels

    def _time_sensitive(func):
        """
        A decorator to ensure we wait long enough for write
        commands to be processed.

        """
        def new_func(*args, **kwargs):
            # Sleep for the required time
            time_waited = time.time() - args[0].last_write_time
            if time_waited < args[0].wait_time:
                time.sleep(args[0].wait_time - time_waited)
            # Run the function and get the new wait time
            args[0].wait_time = func(*args, **kwargs)
            # Update the write time
            args[0].last_write_time = time.time()
            return
        return new_func
            
    @_time_sensitive            
    def set_pattern_bits(self, pattern_number, start_position, data_bits):
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
        self.write(command_string)
        return 0.002*len(data_bits)/4.0 # time to wait until can run again

    def init_channel(self, pattern_number, data_bits=None):
        """
        Re-sets the given row's pattern to the given pattern.

        If the pattern is < 64 bits long, the extra bits will be 0's.
        If no data_bits are given, simply resets the channels' pattern to 0's.

        """
        self.set_pattern_bits(pattern_number, 0, "0"*64)
        if data_bits is not None:
            self.set_pattern_bits(pattern_number, 0, data_bits)

    def init_all_channels_slow(data_generator, data_dict, num_patterns=12):
        """
        Set all the channels according to the bitstring in data_dict[pattern_num].

        If a particular pattern number is not specified, reset it to 0's.

        """
        for pattern_num in range(num_patterns):
            bit_string = data_dict.get(pattern_num, None) # default to None if data_dict[pattern_num] does not exist
            init_channel(data_generator, pattern_num, bit_string)

    def init_all_channels(self, start_address, data_matrix):
        """
        Sets all of the channels according to the bitstring in data_matrix[pattern_num].

        <start_address> is the "column" or bit number to start at (0 to 65535).
        data_matrix must be a 36-item list of strings of 1's and 0's, all of the same length.

        """
        if len(data_matrix) != DataGenerator.number_of_channels:
            raise ValueError("data_matrix must have 36 entries, 1 for each channel")

        # Set up the format of the command
        command_string_template = "data:pattern:word {address},{length},{data};"
        # Assemble the arguments address, length, and data
        args = {}
        args['address'] = start_address
        # length is the number of columns to write (i.e. length of 1 string)
        args['length'] = len(data_matrix[0])
        # data format is "#{num_digits_in_num_bytes}{num_bytes}<byte 1>...<byte n>
        data_string = "#"
        num_bytes = args['length']*5
        num_digits_in_num_bytes = len(str(num_bytes))
        data_string += str(num_digits_in_num_bytes) + str(num_bytes)
        bit_string = ""

        # each set of 5 bytes is of the form <0000><35-32><31-24>...<7-0>
        # where the numbers represent the row number (channel/pattern number)
        # and the first set of 5 bytes is for the first column, 2nd for 2nd, etc.
        try:
            for i in range(args['length']):
                bit_string += "0000"
                for pattern_num in reversed(range(len(data_matrix))): # should be range(36) always
                    bit_string += data_matrix[pattern_num][i]
        except IndexError:
            raise ValueError("all rows (strings) of data_matrix must be of the same length")
        for i in range(0, len(bit_string), 8):
            bits = bit_string[i:i+8]
            byte = chr(int(bits, 2))
            data_string += byte
        args['data'] = data_string
        command_string = command_string_template.format(**args)
        self.write(command_string)
        return 0

    def start(self):
        """
        Send the command to start outputting data.

        """
        self.write("start")

    def stop(self):
        """
        Send the command to stop outputting data.

        """
        self.write("stop")

    def update(self):
        """
        Send the command to update the data output.

        """
        self.write("data:update")

#init_all_channels_slow(data_generator, data_dict)
#init_all_channels(data_generator, 0, data_matrix)

data_dict = {3:"100000011000000110000001100000011000110010000001100000011000000110000001100000011000000100100110011100011100010001101001110100001000000110000001",5:"10"*32, 6:"0"*32+"1"*32, 9:"1"*32+"0"*32}
data_matrix = ["00001" for i in xrange(36)]
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
