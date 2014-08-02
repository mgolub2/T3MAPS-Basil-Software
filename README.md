atlas_usbpix_control
====================

Controlling a T3MAPS pixel detector using USBpix board, basil and python.

Setup instructions for hardware
------------------------

- USB cable from MultiIO to computer
- 2x2 Molex from FE-I4 adapter card to 2V power supply, expecting <70 mA of
current. (Usually approximately 50 mA.)
- 4x2 Molex from FE-I4 adapter card to T3MAPS GND of DO_OUT_P(5) and
  DO_OUT_P(4).
- Connect T3MAPS power (red+black jacks) to GD and VD1 pins on FE-I4 adapter
  card (near 2x2 Molex power input). Black end = GD, white = VD1.
- Connect T3MAPS pins to FE-I4 pins in the following way. Make sure the
  connectors are oriented the correct way on the ribbon so corresponding
  colors are actually connected (and not inverted). The connections on
  T3MAPS go on the INSIDE pin of the 2-pin pair. The outside pin is for
  ground.

    FE-I4 ADAPTER CARD PIN     CABLE COLOR              T3MAPS PIN

    GNDD (near DobOutP)-------BLACK--------------------GND of GCfgDout

    GNDD (near DobOutP)-------PINK---------------------GND of PrmpVbp

    IoMxIn2-------------------BROWN--------------------SRIN_ALL

    SelCmd--------------------RED----------------------SRCK_G

    IoMxOut0------------------GREY(END OF CONNECTOR)---SR_OUT

    IoMxIn3-------------------YELLOW-------------------GCfgCK

    IoMxIn1-------------------GREEN--------------------Dacld

    IoMxSel1------------------PALE BLUE----------------Stbld

- Connect bias cable to the LEMO jack. It should be a -4V bias.

Testing the connections
-----------------------

To test the T3MAPS to make sure everything is set up correctly, run `python
test_multi_column.py`. This program sends a unique pattern to each column of
the chip and then reads it back out. If this test fails, there are incorrect
connections.

Running scan viewer
---------------------

The viewer is located in the scan_analysis.py file. Execute it with

    $ python scan_analysis.py [--persist]

There will be noise on startup. If you are in persist mode, clear the noise
with x. It takes a complete cycle before the viewer resets. Note that the
history function and persistence are completely separate, so clearing the
persistence does not affect the history.
