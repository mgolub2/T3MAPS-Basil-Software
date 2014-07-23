"""
Module lt3maps.

Author: Sam Kohn <kohn@berkeley.edu>

This module enables communication between Python and hardware using the
BASIL framework developed by SiLab, University of Bonn, Germany.

See the class T3MAPSDriver description for more information.

"""
import yaml
import numpy as np
import time
from bitarray import bitarray

from basil.dut import Dut


class Block(dict):
    """
    A class for storing patterns to be written to the chip.

    """
    type = None


class T3MAPSDriver(Dut):
    """
    A class for communicating with a T3MAPS chip.

    This class manages all communications between the programmer and the
    hardware. It knows about configuration registers, injection, pixel
    registers, and clocks.

    It is implemented as a subclass of basil.dut.Dut, the base
    class of the BASIL framework from SiLab, University of
    Bonn, Germany. The documentation for BASIL is available at
    <https://silab-redmine.physik.uni-bonn.de/projects/basil/wiki>. In
    particular, this class is based on the Pixel example, so to learn
    about why certain methods are implemented the way they are, start
    from that example.

    To configure the data structures the software uses, provide a YAML
    file (<http://en.wikipedia.org/wiki/YAML>) which is based off
    lt3maps.yaml. There are instructions in that file's comments for how
    the file is interpreted.

    A minimum working example looks like the following:

    >>> chip = T3MAPSDriver("config.yaml")
    >>> chip.set_configuration_register(column_address=5)
    >>> chip.write_configuration_reg()
    >>> chip.set_pixel_register("10"*32)
    >>> chip.write_pixel_reg()
    >>> chip._run_seq()
    >>> output = chip._get_sr_output()
    >>> print "output:", output

    """

    _blocks = []
    """
    A list of pattern sets (blocks) to send to the chip.

    Each block is a complete command, including shift register input,
    load commands, and enable commands.

    Note: enable commands are not sent to the chip, but rather are
    interpreted by the FPGA as a sign to send a clock signal to the
    chip.

    """
    _block_lengths = {}
    """
    A dict associating command types to the size of the command.

    Command types could be e.g. "inject," "global" (register) or "pixel"
    (register). The size of the command is in bits.

    """
    _global_dropped_bits = 0
    """
    For debugging only. Changes the offset of configuration commands.

    """

    def __init__(self, conf_file_name=None, voltage=1.5, conf_dict=None):
        """
        Initializes the chip, including turning on power.

        Exactly one of conf_file_name and conf_dict must be specified.

        This method also initializes the block lengths to their
        appropriate values.
        """
        if not (bool(conf_file_name) != bool(conf_dict)):
            raise ValueError("conf_file_name xor conf_dict must be specified.")
        elif conf_file_name:
            # Read in the configuration YAML file
            stream = open(conf_file_name, 'r')
            conf_dict = yaml.load(stream)
        else:  # conf_dict must be specified
            pass

        # Create the T3MAPSDriver object
        Dut.__init__(self, conf_dict)

        try:
            # Initialize the chip
            self.init()
        except NotImplementedError:  # this is to make simulation not fail
            print 'chip.init() :: NotImplementedError'

        # turn on the adapter card's power
        self['PWR']['EN_VD1'] = 1
        self['PWR']['EN_VD2'] = 1
        self['PWR']['EN_VA1'] = 1
        self['PWR']['EN_VA2'] = 1
        self['PWR'].write()

        # Set the output voltage on the pins
        self['PWRAC'].set_voltage("VDDD1", voltage)
        self['PWRAC'].set_voltage("VDDD2", voltage)

        # Set the "block lengths" for commands to pixel and global registers
        self._block_lengths['pixel'] = len(self['PIXEL_REG'])
        # 2 extra for load commands, 1 for the 'dropped' bit due to clock
        self._block_lengths['global'] = len(self['GLOBAL_REG']) + 2 +\
            self._global_dropped_bits
        # arbitrary length, but long enough to be detected by discriminator.
        self._block_lengths['inject'] = 500

        # Make sure the chip is reset
        self.reset_seq()

    def write_global_reg(self, position=None, load_DAC=False):
        """
        Add the global register to the command to send to the chip.

        Includes enabling the clock, and loading the Control (CTR)
        and DAC shadow registers. By default, the DAC register is NOT
        loaded. To load it, set the load_DAC parameter to True.

        """

        gr_size = len(self['GLOBAL_REG'][:])  # get the size
        # define start and stop indices in the array
        seq = {
            'SHIFT_IN': bitarray('0' * (gr_size + self._global_dropped_bits)),
            'GLOBAL_SHIFT_EN': bitarray('0' * (gr_size +
                                        self._global_dropped_bits)),
            'GLOBAL_CTR_LD': bitarray('0' * (gr_size + 2 +
                                      self._global_dropped_bits)),
            'GLOBAL_DAC_LD': bitarray('0' * (gr_size + 2 +
                                      self._global_dropped_bits)),
        }
        seq = Block(seq)
        seq.type = 'global'

        # input is the contents of global register
        seq['SHIFT_IN'][self._global_dropped_bits:gr_size +
                        self._global_dropped_bits] =\
            self._global_reg_reversed()
        # Enable the clock
        seq['GLOBAL_SHIFT_EN'][0:gr_size + self._global_dropped_bits] =\
            bitarray(gr_size * '1')
        # load signals into the shadow register
        seq['GLOBAL_CTR_LD'][gr_size + 1 +
                             self._global_dropped_bits:gr_size + 2 +
                             self._global_dropped_bits] = bitarray("1")
        if load_DAC:
            seq['GLOBAL_DAC_LD'][gr_size + 1 +
                                 self._global_dropped_bits:gr_size + 2 +
                                 self._global_dropped_bits] = bitarray("1")

        # Make all patterns the same length
        # Find the max of all lengths of all patterns
        max_length = len(max(seq.values(), key=len))
        # Adjust the length of each pattern
        for value in seq.itervalues():
            length = len(value)
            relative_length = max_length - length
            value += '0' * relative_length

        # add the block to the list of blocks to write
        if position:
            self._blocks.insert(position, seq)
        else:
            self._blocks.append(seq)

    def write_pixel_reg(self, position=None):
        """
        Add the pixel register to the command to send to the chip.

        Includes enabling the clock.

        """
        px_size = len(self['PIXEL_REG'][:])  # get the size
        seq = {
            'SHIFT_IN': bitarray('0' * px_size),
            'PIXEL_SHIFT_EN': bitarray('0' * px_size),
        }
        seq = Block(seq)
        seq.type = 'pixel'

        # this will be shifted out
        seq['SHIFT_IN'][0:px_size] = self['PIXEL_REG'][:]
        # this is to enable clock (12MHz)
        seq['PIXEL_SHIFT_EN'][0:px_size] = bitarray(px_size * '1')

        # add the block to the list of blocks to write
        if position:
            self._blocks.insert(position, seq)
        else:
            self._blocks.append(seq)

    def write_injection(self, delay_until_rise):
        """
        Add an injection pattern (low then high) to the signal.

        `delay_until_rise` tells how many bits to wait until high again.
        Should be less than the expected time till the next injection.
        """
        if delay_until_rise > self._block_lengths['inject']:
            raise ValueError("delay must be <= " +
                             str(self._block_lengths['inject']))

        filler = self._block_lengths['inject'] - delay_until_rise
        injection_sequence = Block({
            "INJECTION": bitarray('0'*delay_until_rise + '1' * filler)
            })
        injection_sequence.type = 'inject'
        self._blocks.append(injection_sequence)

    def run(self, get_output=True):
        """
        Send current commands to the chip and return the output.

        The current blocks are erased in the process. The output is presented
        in the order it is received, i.e. first bit out is output[0]. This
        first bit corresponds to the last bit in the shift register, since the
        last bit is out first.

        """
        # run
        self._run_seq()

        output = None
        if get_output:
            # capture the output from earlier shift registers
            output = self._get_sr_output(invert=True)

        # reset the sequence to start again
        self.reset_seq()
        return output

    def _run_seq(self, num_executions=1, enable_receiver=True):
        """
        Send all commands to the chip.

        if(enable_receiver) (true by default), stores the
        output (by byte) in self['DATA'], retrievable via
        `chip['DATA'].get_data()`.

        if num_executions > 0, run that many times (hardware loop).
        if num_executions == 0, loop indefinitely.

        """
        # enable receiver it work only if pixel register is enabled/clocked
        self['PIXEL_RX'].set_en(enable_receiver)

        # Transcribe the blocks to self['SEQ']
        num_bits = self._write_blocks_to_seq()

        # Write the sequence to the sequence generator (hw driver)
        self['SEQ'].write(num_bits)  # write pattern to memory

        self['SEQ'].set_size(num_bits)  # set size
        self['SEQ'].set_repeat(num_executions)  # set repeat
        self['SEQ'].start()  # start

        while not self['SEQ'].get_done():
            time.sleep(0.01)
            print "Wait for done..."

    def _write_blocks_to_seq(self):
        """
        Write the commands stored in _blocks to self['SEQ'].

        Includes some empty space between blocks to separate commands.

        Returns the number of bits which should be sent to
        self['SEQ'].set_size.

        """
        seq = self['SEQ']

        # set up the INJECTION channel to be all high
        seq['INJECTION'].setall(True)
        # Add each block to self['SEQ']
        num_bits = 0
        buffer_length = 40
        start_location = 0
        end_location = 0
        num_bits_in_seq = 0
        for i, block in enumerate(self._blocks):
            # First find the type of block: pixel or global
            # This determines the length of the block
            num_bits_in_seq = self._block_lengths[block.type]
            end_location = start_location + num_bits_in_seq

            # can't start a SEQ with an injection,
            # since injection signals are low, and
            # the default is high.
            # Fix by moving first block forwards by 1 injection block.
            if start_location == 0 and block.type == 'inject':
                start_location += self._block_lengths[block.type]
                end_location += self._block_lengths[block.type]
                num_bits_in_seq += self._block_lengths[block.type]

            # Write each of the fields of the block to self['SEQ']
            for key, value in block.iteritems():
                seq[key][start_location:end_location] = value

            # record how many bits were written
            num_bits += num_bits_in_seq + buffer_length

            # Move the next start location
            start_location = end_location + buffer_length

        return num_bits

    def reset_seq(self, fields=None):
        """
        Erase all data which was previously set up to go to the chip.

        This is sufficient to make the T3MAPSDriver object's outputs behave as
        if the object is new. It does not affect the object's inputs, in
        particular the input from the shift register's output.

        Options for fields are the fields of the SEQ register specified
        in the YAML configuration file. For example, they could be:

        - SHIFT_IN
        - GLOBAL_SHIFT_EN
        - GLOBAL_CTR_LD
        - GLOBAL_DAC_LD
        - PIXEL_SHIFT_EN
        - INJECTION
        - NOT_USED_0
        - NOT_USED_1

        If no fields are given, resets all fields (entire register).

        """
        if not fields:
            fields = [track['name'] for track in self['SEQ']._conf['tracks']]

        for field in fields:
            self['SEQ'][field].setall(False)

        self._blocks = []

    def set_global_register(self, empty_pattern="10000001", **kwargs):
        """
        Set the values in the global register using keyword arguments.

        Any unspecified fields are initialized to all 0.

        The parameters can be integers or bitarrays. Integers will be
        converted to bitarrays of the appropriate length. They are
        represented as Big-Endian, meaning the leftmost bit gets sent
        first. This matches the convention used by the T3MAPS chip, so
        there is no conversion necessary. Bitarrays should already be
        the appropriate length, so please do not try to assign an 8-bit
        field to bitarray("1"). Instead, use bitarray("00000001"). The
        order of the bits is also Big-Endian, so the leftmost bit is
        sent first.

        `empty_pattern` specifies a set of bits to use as padding for
        sections of the global register which are not used by the chip.
        This behavior is currently hardcoded in, although it would be a
        good improvement to make this behavior adjustable.

        """
        self['GLOBAL_REG'][:] = 0
        for key, value in kwargs.iteritems():
            if isinstance(value, bitarray):
                value.reverse()
            self['GLOBAL_REG'][key] = value

        # assign non-zero value to the unused regions,
        # for debugging purposes
        empties = {
            'EMPTY_0': 32,
            'EMPTY_1': 48,
            'EMPTY_2': 16
        }
        for key, value in empties.iteritems():
            new_pattern = bitarray((empty_pattern * (value/8))[::-1])
            self['GLOBAL_REG'][key] = new_pattern

    def set_pixel_register(self, value):
        """
        Set the value of the pixel register.

        `value` must be a bitarray, string of bits, or iterable of
        booleans. The length must match the length of the register.

        The bits are sent leftmost-first to the chip.

        """
        self['PIXEL_REG'][:] = bitarray(value)

    def _get_sr_output(self, invert=True):
        """
        Retrieve the output from the chip.

        Returned as a list of (possibly inverted) bits.

        Make sure to save the return value, since this method only works
        once.

        """
        # 1. Data emerges from hardware in the following form:
        # [ 0b<nonsense><byte1><byte2>, 0b<nonsense><byte3><byte4>, ...]
        # 2. So, take last 8 bits from each item to get even-numbered entries,
        # 3. and 2nd-to-last 8 bits to get odd-numbered entries.
        # 4. Then, weave the lists together.
        # 5. To get the bits themselves, unpack the uint8's to a list of bits.

        # 1. get data from sram fifo
        rxd = self['DATA'].get_data()
        # 2. Take from rxd only the last 8 bits of each element.
        #    Do this by casting the elements of the list to uint8.
        data0 = rxd.astype(np.uint8)
        # 3. Rightshift rxd 8 bits and take again last 8 bits
        data1 = np.right_shift(rxd, 8).astype(np.uint8)
        # 4. Make data a 1 dimensional array of all bytes read from the FIFO
        #    This magic is accomplished with "FORTRAN" order reshaping.
        data = np.reshape(np.vstack((data1, data0)), -1, order='F')
        # 5. make data into bits
        bdata = np.unpackbits(data)
        if invert:
            # treat bits as bools (default is 8-bit numbers),
            # then recast to ints.
            bdata = np.invert(bdata, dtype=np.bool).astype(np.uint8)
        return bdata

    def _get_output_size(self):
        """
        Returns the number of bits received as output.

        This cannot be called after `_get_sr_output`.

        """
        byte_size = 8
        return byte_size * self['DATA'].get_fifo_size()

    def reset_output(self):
        """
        Reset the sram fifo that receives the output.

        """
        self['DATA'].reset()

    def _global_reg_reversed(self):
        """
        Get the global register, with the bits in each field reversed.

        This is necessary for input to the chip.

        """
        global_register = self['GLOBAL_REG']

        # reverse each field, save the result, then re-reverse
        for field in global_register._fields:
            global_register[field].reverse()

        to_return = global_register[:]

        # now un-reverse the fields to return to normal
        for field in global_register._fields:
            global_register[field].reverse()

        return to_return

class Pixel():
    def __init__(self, column, row):
        self.column = column
        self.row = row
        self.TDAC = 0
        self._TDAC_binary = "00000"

    def update_TDAC(self, strobe_value, enable):
        """
        Update the TDAC value after a strobe.

        `strobe_value` is the value of the 5-bit pattern that was sent to TDAC_strobes.
        `enable` is True if the Pixel's SR bit was 1 for the strobe.

        """
        TDAC_length = 5
        enable_str = str(int(enable))
        new_TDAC_binary = ""
        # Get a binary representation of the strobe
        bin_strobe = bin(strobe_value)[2:]

        for i in range(TDAC_length):
            if bin_strobe[i] == "1":
                new_TDAC_binary += enable_str
            else:
                new_TDAC_binary += self._TDAC_binary[i]

        self._TDAC_binary = new_TDAC_binary
        self.TDAC = int(new_TDAC_binary, 2)



class T3MAPSChip():
    """
    Control the T3MAPS chip with common functions.

    """

    def __init__(self, config_file):
        self._driver = T3MAPSDriver(config_file)

        num_columns = 18
        num_rows = len(self._driver['PIXEL_REG'])
        self._pixels = [[Pixel(column, row) for column in range(num_columns)]
                        for row in range(num_rows)]

    def set_bit_latches(self, column_number, rows_to_enable, *args):
        """
        Set the hit, inject and TDAC latches for the given column.

        If `rows_to_enable` is None, then will enable all rows. To
        disable all rows, set `rows_to_enable` = [].
        To set TDAC strobes, pass 'TDAC_strobes' as an arg, and make
        the next argument be the binary value of the bits to strobe,
        e.g. args = ['TDAC_strobes', 31] strobes all 5 bits.

        """
        driver = self._driver

        # Construct the pixel register input
        PIXEL_REGISTER_LENGTH = len(self._pixels[0])
        pixel_register_input = None
        if rows_to_enable is None:
            pixel_register_input = str(int(enable)) * PIXEL_REGISTER_LENGTH
        else:
            pixel_register_input = ["1" if i in rows else "0" for i in
                                    range(PIXEL_REGISTER_LENGTH)]
            pixel_register_input = ''.join(pixel_register_input)

        driver.set_global_register(
            column_address=column_number)
        driver.write_global_reg()

        driver.set_pixel_register(pixel_register_input)
        driver.write_pixel_reg()

        # construct a dict of strobes to pass to set_global_register
        strobes = {arg: 1 for arg in args if not isinstance(arg, int)}
        if 'TDAC_strobes' in args:
            # there should be exactly 1 int in args: the TDAC value
            tdac = [value for value in args if isinstance(value, int)]
            strobes['TDAC_strobes'] = tdac[0]

        # Enable the strobes
        driver.set_global_register(
            column_address=column_number,
            enable_strobes=1,
            **strobes
            )
        driver.write_global_reg()

        # Disable the strobes. (New values are saved.)
        driver.set_global_register(
            column_address=column_number
            )
        driver.write_global_reg()

        # Update the saved Pixel TDAC values, maybe
        if 'TDAC_strobes' in args:
            for i, enable_str in enumerate(pixel_register_input[::-1]):
                self._pixels[column_number][i].update_TDAC(
                    strobes['TDAC_strobes'], 
                    (enable_str == "1")
                )
        return

    def set_pixel_register(self, value):
        self._driver.set_pixel_register(value)
        self._driver.write_pixel_reg()

    def set_global_register(self, **kwargs):
        load_DAC = False
        if 'load_DAC' in kwargs.keys():
            load_DAC = kwargs['load_DAC']
            kwargs = {key:value for key, value in kwargs.iteritems() if key !=
                      'load_DAC'}

        self._driver.set_global_register(**kwargs)
        self._driver.write_global_reg(load_DAC)

    def run(self, get_output=True):
        return self._driver.run(get_output)

if __name__ == "__main__":
    # create a chip object
    chip = T3MAPSChip("lt3maps.yaml")

    # settings for global register (to input into global SR)
    chip.set_global_register(column_address=8, load_DAC=True)

    # settings for pixel register (to input into pixel SR)
    chip.set_pixel_register('10'*8+'1000'*8+'10000000'*2)

    # send in a different (but nonzero) pattern to get out what we
    # sent in before.
    chip.set_pixel_register('1100'*16)

    # send the commands to the chip and get output back
    output = chip.run()
    print "chip output:"
    print output
