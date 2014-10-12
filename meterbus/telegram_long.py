import json

from .telegram_body import TelegramBody
from .telegram_header import TelegramHeader
from .exceptions import MBusFrameCRCError, MBusFrameDecodeError, FrameMismatch


class TelegramLong(object):
    @staticmethod
    def parse(data):
        if data and len(data) < 9:
            raise MBusFrameDecodeError("Invalid M-Bus length")

        if data[0] != 0x68:
            raise FrameMismatch()

        return TelegramLong(data)

    def __init__(self, dbuf=None):
        self._header = TelegramHeader()
        self._body = TelegramBody()

        tgr = dbuf
        if isinstance(dbuf, basestring):
            tgr = map(ord, dbuf)

        headerLength = self.header.headerLength
        firstHeader = tgr[0:headerLength]

        # Copy CRC and stopByte into header
        resultHeader = firstHeader + tgr[-2:]

        self.header.load(resultHeader)

        if self.header.lField.parts[0] < 3:
            raise MBusFrameDecodeError("Invalid M-Bus length value")

        self.body.load(tgr[headerLength:-2])

        if not self.check_crc():
            raise MBusFrameCRCError(self.compute_crc(),
                                    self.header.crcField.parts[0])

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, value):
        self._header = TelegramHeader()
        self._header.load(value)

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        self._body = TelegramBody()
        self._body.load(value)

    @property
    def records(self):
        """Alias property for easy access to records"""
        return self.body.bodyPayload.records

    def load(self, tgr):
        telegram = tgr

        if isinstance(tgr, basestring):
            telegram = map(ord, tgr)

        headerLength = self.header.headerLength
        firstHeader = telegram[0:headerLength]

        # Copy CRC and stopByte into header
        resultHeader = firstHeader + telegram[-2:]

        self.header.load(resultHeader)
        self.body.load(telegram[headerLength:-2])

    # def parse(self):
    #     self.body.parse()

    def compute_crc(self):
        return (self.header.cField.parts[0] +
                self.header.aField.parts[0] +
                sum(self.body.bodyHeader.ci_field.parts) +
                sum(self.body.bodyHeader.id_nr_field.parts) +
                sum(self.body.bodyHeader.manufacturer_field.parts) +
                sum(self.body.bodyHeader.version_field.parts) +
                sum(self.body.bodyHeader.measure_medium_field.parts) +
                sum(self.body.bodyHeader.acc_nr_field.parts) +
                sum(self.body.bodyHeader.status_field.parts) +
                sum(self.body.bodyHeader.sig_field.parts) +
                sum(self.body.bodyPayload.body.parts)) % 256

    def check_crc(self):
        return self.compute_crc() == self.header.crcField.parts[0]

    def to_JSON(self):
        return json.dumps({
            'head': json.loads(self.header.to_JSON()),
            'body': json.loads(self.body.to_JSON())
        }, sort_keys=False, indent=4)