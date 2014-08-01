atlas_usbpix_control
====================

Controlling a T3MAPS pixel detector using USBpix board, basil and python.

Setup instructions for hardware
------------------------

- USB cable from MultiIO to computer
- 2x2 Molex from FE-I4 adapter card to 2V power supply, expecting <70 mA of
current. (Usually approximately 50 mA.)
- Connect T3MAPS power (red+black jacks) to GD and VD1 pins on FE-I4 adapter
  card (near 2x2 Molex power input).
- Connect T3MAPS pins to FE-I4 pins in the following way. Note the cables are
  listed in the order they appear on the connector. Make sure the connectors
  are oriented the correct way on the ribbon so corresponding colors are
  actually connected (and not inverted). The connections on T3MAPS go on the
  INSIDE pin of the 2-pin pair. The outside pin is for ground.

    FE-I4 ADAPTER CARD PIN     CABLE COLOR              T3MAPS PIN

    GNDD (near DobOutP)-------BLACK--------------------GND of SRIN_ALL
    IoMxIn2-------------------BROWN--------------------SRIN_ALL
    SelCmd--------------------RED----------------------SRCK_G
    IoMxOut0------------------ORANGE-------------------SR_OUT
    IoMxIn3-------------------YELLOW-------------------GCfgCK
    IoMxIn1-------------------GREEN--------------------Dacld
    IoMxSel1------------------PALE BLUE----------------Stbld
