"""
Unittests for eastronSDM630
Uses a dummy serial port from the module :py:mod:`dummy_serial`.
"""
import unittest

import backend.eastronSDM630 as eastronSDM630
import dummy_serial


###########################################
# Communication using a dummy serial port #
###########################################

class TestDummyCommunication(unittest.TestCase):
    def setUp(self):
        # Prepare a dummy serial port to have proper responses
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RESPONSES

        # Monkey-patch a dummy serial port for testing purpose
        eastronSDM630.minimalmodbus.serial.Serial = dummy_serial.Serial

        # Initialize a (dummy) instrument
        self.instrument = eastronSDM630.EastronSDM630('DUMMYPORTNAME', 5)
        self.instrument._debug = False

    # Check Network Baud-rate of 19200 bits/s
    def testReadNetworkBaudRate(self):
        self.assertAlmostEqual(self.instrument.read_network_baud_rate(), 3)

    # Read Import and Export values
    def testReadTotalImport(self):
        self.assertAlmostEqual(self.instrument.read_total_import(), 80.622002, places=3)

    def testReadImportL1(self):
        self.assertAlmostEqual(self.instrument.read_import_L1(), 76.311996, places=3)

    def testReadImportL2(self):
        self.assertAlmostEqual(self.instrument.read_import_L2(), 2.106000, places=3)

    def testReadImportL3(self):
        self.assertAlmostEqual(self.instrument.read_import_L3(), 2.204000, places=3)

    def testReadTotalExport(self):
        self.assertAlmostEqual(self.instrument.read_total_export(), 63092.074219, places=3)

    def testReadExportL1(self):
        self.assertAlmostEqual(self.instrument.read_export_L1(), 20137.281250, places=3)

    def testReadExportL2(self):
        self.assertAlmostEqual(self.instrument.read_export_L2(), 21664.507812, places=3)

    def testReadExportL3(self):
        self.assertAlmostEqual(self.instrument.read_export_L3(), 21290.285156, places=3)


"""A dictionary of respones from a dummy EastronSDM630 instrument.
The key is the message (string) sent to the serial port, and the item is the response (string)
from the dummy serial port.
"""
RESPONSES = dict()

# Message:  slave address, function code 3/4, register address, 1 register, CRC.
# Response: slave address, function code 3/4, 2 bytes, value, CRC
# Note that the string 'AAAAAAA' might be easier to read if grouped,
# like 'AA' + 'AAAA' + 'A' for the initial part (address etc) + payload + CRC.

# read_network_baud_rate(): Return value 3.0 (corresponds to 19200 bits/s)
RESPONSES['\x05\x03\x00\x1c\x00\x02\x04I'] = '\x05\x03\x04@@\x00\x00«ç'

# read_total_import()
RESPONSES['\x05\x04\x00H\x00\x02ðY'] = '\x05\x04\x04B¡>w«\x98'

# read_import_L1()
RESPONSES['\x05\x04\x01Z\x00\x02Q\xa0'] = '\x05\x04\x04B\x98\x9f¾ÂS'

# read_import_L2()
RESPONSES['\x05\x04\x01\\\x00\x02±¡'] = '\x05\x04\x04@\x06È´\x1c2'

# read_import_L3()
RESPONSES['\x05\x04\x01^\x00\x02\x10a'] = '\x05\x04\x04@\r\x0eV¾\x19'

# read_total_export()
RESPONSES['\x05\x04\x00J\x00\x02Q\x99'] = '\x05\x04\x04Gvt\x13-ç'

# read_export_L1()
RESPONSES['\x05\x04\x01`\x00\x02q\xad'] = '\x05\x04\x04F\x9dR\x90\x07î'

# read_export_L2()
RESPONSES['\x05\x04\x01b\x00\x02Ðm'] = '\x05\x04\x04F©A\x04J¿'

# read_export_L3()
RESPONSES['\x05\x04\x01d\x00\x020l'] = '\x05\x04\x04F¦T\x92ôB'

if __name__ == '__main__':
    unittest.main()
