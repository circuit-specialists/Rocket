from machine import UART
from array import *
import utime


class NEO6MGPS(object):
    def __init__(self, baudrate=9600):
        # pin 17 tx, pin 16 rx
        self.uart = UART(2, baudrate)
        # init with given parameters
        self.uart.init(baudrate, bits=8, parity=None, stop=1)

    def update(self):
        self.read_raw()
        self.setValues()

    def read_raw(self):
        self.data = self.uart.read()
        self.data = self.data.splitlines()
        self.data.sort()

    def setValues(self):
        for i in range(0, len(self.data)):
            if (self.data[i].find('GPGGA'.encode()) == 1):
                self.gpgga = self.data[i]
            elif (self.data[i].find('GPGLL'.encode()) == 1):
                self.gpgll = self.data[i]
            elif (self.data[i].find('GPGSA'.encode()) == 1):
                self.gpgsa = self.data[i]
            elif (self.data[i].find('GPGSV'.encode()) == 1):
                self.gpgsv = self.data[i]
            elif (self.data[i].find('GPRMC'.encode()) == 1):
                self.gprmc = self.data[i]
            elif (self.data[i].find('GPVTG'.encode()) == 1):
                self.gpvtg = self.data[i]

    def interpret_rmc(self):
        if (len(self.gprmc) < 23):
            return self.update()
        self.rmc = self.gprmc.split(','.encode())
        self.utc = str(self.rmc[1])[2:-1]
        self.receiver = str(self.rmc[2])[2:-1]
        try:
            self.latitude = float(self.rmc[3]) / 100
        except:
            self.latitude = str(self.rmc[3])[2:-1]
        self.latitude_direction = str(self.rmc[4])[2:-1]
        try:
            self.longitude = float(self.rmc[5]) / 100
        except:
            self.longitude = str(self.rmc[5])[2:-1]
        self.longitude_direction = str(self.rmc[6])[2:-1]
        self.speed = str(self.rmc[7])[2:-1]
        self.cmg = str(self.rmc[8])[2:-1]
        self.fixdata = str(self.rmc[9])[2:-1]
        self.magvar = str(self.rmc[10])[2:-1]
        self.magvardir = str(self.rmc[11])[2:-1]
        self.checksum = str(self.rmc[12])[2:-1]

    def write(self, value):
        self.uart.write(value)

    def writeToArray(self, array):
        self.uart.readinto(array)

    def print_raw_values(self):
        self.raw_values = [
            self.gpgga, self.gpgll, self.gpgsa, self.gpgsv, self.gprmc,
            self.gpvtg
        ]
        for i in range(0, len(self.raw_values)):
            try:
                print(self.raw_values[i])
            except:
                pass

    def getformatedUTC(self, timezone):
        utc = float(self.utc)
        self.hours = int(utc / 10000)
        if(self.hours < 7):
            self.hours += 24
        self.hours += timezone
        utc %= 10000
        self.minutes = int(utc / 100)
        utc %= 100
        self.seconds = int(utc)

        return str(
            str(self.hours) + ":" + str(self.minutes) + ":" +
            str(self.seconds))

    def print_values(self):
        self.value_names = [
            "utc", "latitude", "latitude_direction", "longitude",
            "longitude_direction", "fix_quality", "num_sat_track",
            "horizontal_dilution", "altitude", "altitude_unit",
            "height_above_WGS84", "height_above_WGS84_unit", "last_update",
            "station_ID"
        ]
        self.values = [
            self.utc, self.latitude, self.latitude_direction, self.longitude,
            self.longitude_direction, self.fix_quality, self.num_sat_track,
            self.horizontal_dilution, self.altitude, self.altitude_unit,
            self.height_above_WGS84, self.height_above_WGS84_unit,
            self.last_update, self.station_ID
        ]
        for i in range(0, len(self.values)):
            try:
                print(self.value_names[i] + ":    " + str(self.values[i]))
            except:
                pass
