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

'''
    @description: 获取VNA在某个点的数据
    @param {
        int f_min: 频率的最小值
        int f_max: 频率的最大值
        int f_numpoints: 频率的步幅
    }
    @return {
        float [[f, real, imaginary], ...] 获取到的数据，分为频率，实部，虚部
    }
'''
def get_vnadata(f_min = 10000000000, f_max = 18000000000, f_numpoints = 100): 
    try:
        f_min = int(f_min)
        f_max = int(f_max)
        f_numpoints = int(f_numpoints)

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
        print("[VNA info]", myPna.read())

        # check the error queue
        myPna.write("SYST:ERR?")
        print("[VNA info]", myPna.read())

        # Select the default measurement name as assigned on preset. To catalog the measurement names,
        # by channel number, use the 'CALCulate[n]:PARameter:CATalog?' command where [n] is the channel
        # number. The channel number, n, defaults to "1" and is optional.
        # Measurement name is case sensitive.
        myPna.write("CALC:PAR:SEL 'CH1_S11_1'")

        # Set data transfer format to ASCII
        myPna.write("FORM:DATA ASCII")

        # Alter measure from S11 to S21
        myPna.write("CALC:PAR:MOD S21")

        myPna.write("SENSe:SWEep:TYPE LIN")

        FREQ_START = f_min
        FREQ_STOP  = f_max

        myPna.write("SENSe:FREQ:STARt " + str(FREQ_START))

        myPna.write("SENSe:FREQ:STOP " + str(FREQ_STOP))

        myTraceData = []

        # Set number of points by list value
        numPoints = f_numpoints
        # numPoints = int((FREQ_STOP - FREQ_START) / f_step)
        myPna.write("SENS:SWE:POIN " + str(numPoints) + ";*OPC?")
        myPna.read()

        # Trigger assertion with hold-off for trigger complete via *OPC?
        myPna.write("SENS:SWE:MODE SING;*OPC?")
        myPna.read()

        # The SDATA assertion queries underlying real and imaginary pair data
        myPna.write("CALC:DATA? SDATA")
        myTraceData = myPna.read()


        DataList = myTraceData.split(',')
        FREQ_STEP = (FREQ_STOP - FREQ_START)/(numPoints)
        Data_res = []
        for index in range(numPoints):
            data_tmp = [str(FREQ_START+FREQ_STEP*index), DataList[2*index], DataList[2*index+1]]
            Data_res.append(data_tmp)

        # Check the error queue. Initially *CLS asserted in beginning of program.
        # The application should run from stem to stern error free. The final error
        # queue query should return '+0, No Error', else the application has potentially
        # caused a correctable error!.
        myPna.write("SYST:ERR?")
        print("[VNA info]", myPna.read())

        # Close the VISA connection
        myPna.close()
        return Data_res

    except Exception as err:
        print("[Get VNA Data Error]", err)
        return [['NULL', 'NULL', 'NULL']]
    pass

if __name__ == "__main__": 
    data = get_vnadata()
    print(data)
