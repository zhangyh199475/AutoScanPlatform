# -*- coding: utf-8 # Python for Test and Measurement
#
# #
# # Requires PyVISA to use VISA in Python
# # 'http://pyvisxxa.sourceforge.net/pyvisa/'
#
# # Keysight IO Libraries IO Libraries Suite
##  'https://www.keysight.com.cn/cn/zh/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html'
#

import pyvisa
import time
# import os
# os.add_dll_directory('C:\\Program Files (x86)\\Keysight\\IO Libraries Suite\\bin')

# Main application code
try:

    # Open a VISA resource manager pointing to the installation folder for the Keysight Visa libraries.
    rm = pyvisa.ResourceManager('C:\\Program Files (x86)\\IVI Foundation\\VISA\\WinNT\\agvisa\\agbin\\visa32.dll')

    # Based on the resource manager, open a sesion to a specific VISA resource string as provided via
    #   Keysight Connection Expert
    # ALTER LINE BELOW - Updated VISA resource string to match your specific configuration
    myPna = rm.open_resource("TCPIP0::169.254.114.102::hislip0::INSTR")

    # Set Timeout - 10 seconds
    myPna.timeout = 10000

    # Preset the PNA and wait for preset completion via use of *OPC?
    # *OPC? holds-off subsequent commands and places a "1" on the output buffer
    # when the predicating command functionality is complete. Do not use a loop
    # with *OPC? as there is no change from a 0 condition to a 1 condition.
    # A '1' is placed on the output buffer when the operation is complete.
    myPna.write("SYST:PRES; *OPC?")
    myPna.read()

    # Clear the event status registers and empty the error queue
    myPna.write("*CLS")

    # Query identification string *IDN?
    myPna.write("*IDN?")
    print(myPna.read())

    # check the error queue
    myPna.write("SYST:ERR?")
    print(myPna.read())

    # Select the default measurement name as assigned on preset. To catalog the measurement names,
    # by channel number, use the 'CALCulate[n]:PARameter:CATalog?' command where [n] is the channel
    # number. The channel number, n, defaults to "1" and is optional.
    # Measurement name is case sensitive.
    myPna.write("CALC:PAR:SEL 'CH1_S11_1'")

    # Set data transfer format to ASCII
    myPna.write("FORM:DATA ASCII")

    # Alter measure from S11 to S21
    #myPna.write("CALC:PAR:MOD S21")

    myPna.write("SENSe:SWEep:TYPE LIN")

    FREQ_START = 10000000000
    FREQ_STOP  = 18000000000

    myPna.write("SENSe:FREQ:STARt " + str(FREQ_START))

    myPna.write("SENSe:FREQ:STOP " + str(FREQ_STOP))

    myTraceData = []

    # Set number of points by list value
    numPoints = 201
    myPna.write("SENS:SWE:POIN " + str(numPoints) + ";*OPC?")
    myPna.read()

    startTime = time.clock()
    # Trigger assertion with hold-off for trigger complete via *OPC?
    myPna.write("SENS:SWE:MODE SING;*OPC?")
    myPna.read()

    stopTime = time.clock() - startTime

    # The SDATA assertion queries underlying real and imaginary pair data
    myPna.write("CALC:DATA? SDATA")
    myTraceData = myPna.read()

    # print("Time to sweep = " + str(stopTime))
    # print("Number of trace points set = " + str(numPoints))
    # print("Number of characters in returned data " + str(len(myTraceData)))
    # print(myTraceData)

    DataList = myTraceData.split(',')

    f = open(r"./Data/test.csv", "w")
    f.write('!File: Measurement: S11\n')
    f.write('# Hz,R,I\n')
    FREQ_STEP = (FREQ_STOP - FREQ_START)/(numPoints-1)
    for index in range(numPoints):
        f.write(str(FREQ_START+FREQ_STEP*index)+',')
        f.write(DataList[2*index] + ',' + DataList[2*index+1]+'\n')

    f.close()

    # Check the error queue. Initially *CLS asserted in beginning of program.
    # The application should run from stem to stern error free. The final error
    # queue query should return '+0, No Error', else the application has potentially
    # caused a correctable error!.
    myPna.write("SYST:ERR?")
    print(myPna.read())

    # Close the VISA connection
    myPna.close()

except Exception as err:
    print("Exception: " + str(err))
