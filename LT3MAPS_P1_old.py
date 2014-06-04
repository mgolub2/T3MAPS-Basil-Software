"""
Hardware-specific implementation of Chip class to control the LT3Maps_P1 chip.

"""

from shiftregister import Chip
import visa

class ChipWithInstruments(Chip):
    """
    Control the LT3Maps_P1 chip using data generator, signal generator, and counter.

    """

    def __init__(self):
        self.function_generator = visa.GpibInstrument("GPIB::5",board_number=0)
        self.data_generator = visa.GpibInstrument("GPIB::3", board_number=0)
        self.counter = visa.GpibInstrument("GPIB::10", board_number=0)
        #self.function_generator.write("VOLT 0.2")
        self.data_generator.ask("DISP?")
