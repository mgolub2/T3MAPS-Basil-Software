#
# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
#
# SVN revision information:
#  $Rev::                       $:
#  $Author::                    $:
#  $Date::                      $:
#

import yaml
import numpy as np
import time
from bitarray import bitarray

from basil.dut import Dut

class Pixel(Dut):
    """
    A class for communicating with a pixel chip.

    """

    cursor = 0
    """
    The current location to insert new commands.

    """

    def __init__(self, conf_file_name=None, voltage=1.2, conf_dict=None):
        """
        Initializes the chip, including turning on power.

        Exactly one of conf_file_name and conf_dict must be specified.
        """
        if not (bool(conf_file_name) != bool(conf_dict)):
            raise ValueError("Exactly one of conf_file_name and conf_dict must be specified.")
        elif conf_file_name:
            # Read in the configuration YAML file
            stream = open("lt3maps.yaml", 'r')
            conf_dict = yaml.load(stream)
        else: # conf_dict must be specified
            pass

        # Create the Pixel object
        #chip = Pixel(conf_dict)
        Dut.__init__(self,conf_dict)

        try:      
            # Initialize the chip
            self.init()
        except NotImplementedError: # this is to make simulation not fail
            print 'chip.init() :: NotImplementedError'
            
        # turn on the adapter card's power
        self['PWR']['EN_VD1'] = 1
        self['PWR']['EN_VD2'] = 1
        self['PWR']['EN_VA1'] = 1
        self['PWR']['EN_VA2'] = 1
        self['PWR'].write()

        # Set the output voltage on the pins
        self['PWRAC'].set_voltage("VDDD1",1.5)
        self['PWRAC'].set_voltage("VDDD2",1.5)
        print "VD1:", self['PWRAC'].get_voltage("VDDD1"), "V", self['PWRAC'].get_current("VDDD1"), "A"

        # Make sure the chip is reset
        self.reset()
    def write_global_reg(self, location=None, load_DAC=False):
        """
        Add the global register to the command to send to the chip.

        Loads the values of self['GLOBAL_REG'] into the ['SEQ'] register.
        Includes enabling the clock, and loading the Control (CTR)
        and DAC shadow registers.

        If `location` is not specified, then the current value of
        `self.cursor` is used.

        """
        
        if not location:
            location = self.cursor

        gr_size = len(self['GLOBAL_REG'][:]) #get the size
        # define start and stop indices in the array
        start_location = location
        stop_location = location + gr_size
        seq = self['SEQ']
        # input is the contents of global register
        seq['SHIFT_IN'][start_location:stop_location] = self['GLOBAL_REG'][:]
        # Enable the clock
        seq['GLOBAL_SHIFT_EN'][start_location:stop_location] = bitarray( gr_size * '1')
        # load signals into the shadow register
        seq['GLOBAL_CTR_LD'][stop_location + 1:stop_location + 2] = bitarray("1")
        if load_DAC:
            seq['GLOBAL_DAC_LD'][stop_location + 1:stop_location + 2] = bitarray("1")
        
        
        # Execute the program (write bits to output pins)
        # + 1 extra 0 bit so that everything ends on LOW instead of HIGH
        #self._run_seq(gr_size+3)
    
    def write_pixel_reg(self, location=None):
        """
        Add the pixel register to the command to send to the chip.

        Loads the values of self['PIXEL_REG'] into the ['SEQ'] register.
        Includes enabling the clock.

        If `location` is None, uses current value of `self.cursor`.

        """
        if not location:
            location = self.cursor

        px_size = len(self['PIXEL_REG'][:]) #get the size
        start_location = location
        stop_location = location + px_size
        self['SEQ']['SHIFT_IN'][start_location:stop_location] = self['PIXEL_REG'][:] # this will be shifted out
        self['SEQ']['PIXEL_SHIFT_EN'][start_location:stop_location] = bitarray( px_size * '1') #this is to enable clock (12MHz)

        #self._run_seq(px_size+1) #add 1 bit more so there is 0 at the end other way will stay high
            
    def run_seq(self, size, num_executions=1, enable_receiver=True):
        """
        Send the contents of self['SEQ'] to the chip and wait until it finishes.

        if(enable_receiver), stores the output (by byte) in
        self['DATA'], retrievable via `chip['DATA'].get_data()`.

        """
        #enable receiver it work only if pixel register is enabled/clocked
        chip['PIXEL_RX'].set_en(enable_receiver) 
        
        # Write the sequence to the sequence generator (hw driver)
        self['SEQ'].write(size) #write pattern to memory

        
        self['SEQ'].set_size(size)  # set size
        self['SEQ'].set_repeat(num_executions) # set repeat
        self['SEQ'].start() # start
        
        while not chip['SEQ'].get_done():
            time.sleep(0.01)
            print "Wait for done..."

    def reset(self, seq_fields=None):
        """
        Reset the given fields of the ['SEQ'] register to all 0's.

        If no fields are given, resets all fields (entire register).

        """
        if not seq_fields:
            seq_fields = [track['name'] for track in self['SEQ']._conf['tracks']]

        for field in seq_fields:
            self['SEQ'][field].setall(False)

    def set_global_register(self, **kwargs):
        """
        Assign the values in given as parameters to the fields
        in ['GLOBAL_REG'].

        The values can be integers or bitarrays.

        """
        for key, value in kwargs.iteritems():
            self['GLOBAL_REG'][key] = value

    def set_pixel_register(self, value):
        """
        Assign the given `value` to ['PIXEL_REG'].

        `value` must be a bitarray, string of bits, or iterable
        of booleans. The length must match the length of the
        register.

        """
        self['PIXEL_REG'][:] = bitarray(value)

    def get_sr_output(self, invert=False):
        """
        Retrieve the output from the chip.

        Returned as a list of (possibly inverted) bits.

        """
        # 1. Data emerges from hardware in the following form:
        # [ 0b<nonsense><byte1><byte2>, 0b<nonsense><byte3><byte4>, ...]
        # 2. So, take last 8 bits from each item to get even-numbered entries,
        # 3. and 2nd-to-last 8 bits to get odd-numbered entries.
        # 4. Then, weave the lists together.
        # 5. To get the bits themselves, unpack the uint8's to a list of bits.

        #1. get data from sram fifo
        rxd = self['DATA'].get_data()
        # 2. Change type to unsigned int 8 bits and take from rxd only the last 8 bits
        data0 = rxd.astype(np.uint8)
        # 3. Rightshift rxd 8 bits and take again last 8 bits
        data1 = np.right_shift(rxd, 8).astype(np.uint8)
        # 4. make data a 1 dimensional array of all bytes read from the FIFO
        data = np.reshape(np.vstack((data1, data0)), -1, order='F')
        # 5. make data into bits
        bdata = np.unpackbits(data)
        if invert:
            # treat bits as bools (default is 8-bit numbers),
            # then recast to ints.
            bdata = np.invert(bdata, dtype=np.bool).astype(np.uint8)
        return bdata

    def get_output_size(self):
        """
        Returns the number of bits received as output.

        """
        byte_size = 8
        return byte_size * self['DATA'].get_fifo_size()

if __name__ == "__main__":
    # create a chip object
    chip = Pixel("lt3maps.yaml")

    #settings for global register (to input into global SR)
    chip.set_global_register(config_mode=3, column_address=8)

    print "program global register..."
    chip.write_global_reg(location=0, load_DAC=True)


    #settings for pixel register (to input into pixel SR)
    chip.set_pixel_register('10'*8+'1000'*8+'10000000'*8+'1000000000000000')

    print "program pixel register..."
    chip.write_pixel_reg(location=150)

    chip.set_pixel_register('1100'*32)

    chip.write_pixel_reg(location=320)

    # send the commands to the chip
    chip.run_seq(500, num_executions=1)

    # Get output back
    print "chip output size:", chip.get_output_size()
    print "chip output:"
    print chip.get_sr_output(invert=True)
