'''
Created on 25.04.2016

@author: jrenken
'''

import datetime
from parser import Parser
from nmea import NmeaRecord


class AisParser(Parser):
    '''
    Parser for AIS Position Report Class A and B
    Type 1, 2 and 3 messages share a common reporting structure

    '
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(AisParser, self).__init__()
        self.binaryPayload = ''
        self.fragment = 0
        self.fragmentcount = 0

    def parse(self, data):
        if not data[3:6] in ('VDM', 'VDO'):
            return {}
        nmea = NmeaRecord(data)
        if nmea.valid:
            fcnt = nmea.value(1)
            frag = nmea.value(2)

            if frag == 1:
                self.binaryPayload = nmea[5]
            else:
                self.binaryPayload += nmea[5]

            if frag == fcnt:
                return self.decodePayload(self.binaryPayload)
            return {}

    def decodePayload(self, payload):
        binPayload = BitVector(payload)

        try:
            mmsi = binPayload.getInt(8, 30)
            type = binPayload.getInt(0, 6)
            if type in (1, 2, 3):
                bs = {'lat': 89, 'lon': 61, 'ts': 137, 'head': 128, 'cog': 116}
            elif type in (18, 19):
                bs = {'lat': 85, 'lon': 57, 'ts': 133, 'head': 124, 'cog': 112}
            else:
                return {}

            result = {'id': mmsi,
                      'lat': float(binPayload.getInt(bs['lat'], 27)) / 600000.0,
                      'lon': float(binPayload.getInt(bs['lon'], 28)) / 600000.0,
                      'depth': 0.0}
            sec = binPayload.getInt(bs['ts'], 6)
            dt = datetime.datetime.utcnow()
            if sec < 60:
                dt.replace(second=sec)
            result['time'] = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
            head = binPayload.getInt(bs['head'], 9)
            if head == 511:
                head = 0.1 * float(binPayload.getInt(bs['cog'], 12))
            result['heading'] = head
            return dict((k, v) for k, v in result.iteritems() if v is not None)
        except (ValueError, KeyError, IndexError):
            return {}


class BitVector:
    '''
    Helper class for handling AIS binary payload data
    '''

    def __init__(self, val=0, size=0):
        '''
        constructor
        :param val: either an integer or a 6bit encoded string
        :type val: integer, long or string
        :param size: number of bit contained in val if val is int or long
        :type size: int
        '''
        self.vector = []
        if type(val) is str:
            for c in val:
                self.append6Bit(c)
        elif type(val) in (int, long) and size:
            self.extend(val, size)

    def extend(self, val, size):
        if size:
            if size > 32:
                raise ValueError('Too many bits. Maximum is 32')
            fmt = '{0:0%ib}' % size
            l = list(map(int, fmt.format(val)))
            self.vector.extend(l)

    def append6Bit(self, ch):
        ''' return s the 6 bit binary value of a hex decoded bit field as used in AIS sentences
        :param ch: character
        :type ch: unsigned char
        :return 6 bit value
        '''
        res = ord(ch) - 48
        if res > 40:
            res -= 8
        self.extend(res, 6)

    def __len__(self):
        return len(self.vector)

    def __str__(self):
        return str(self.vector)

    def getInt(self, start, size):
        'get integer value from a slice'
        if size > 32:
            raise ValueError("Maximum size is 32 bit")
        if start + size > len(self.vector):
            raise KeyError("Size extends vector size")
        result = int()
        mask = int(1) << size
        for i in range(start, start + size):
            mask >>= 1
            if self.vector[i]:
                result |= mask
        return result

if __name__ == "__main__":
    p = AisParser()
    print p.parse('!AIVDM,1,1,,A,139cJd>P1IPWunbNI:nsdOvrRHAH,0*24')
