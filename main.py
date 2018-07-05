import machine
import neo6mgps
import bme280
import mpu9250
from microWebSrv import MicroWebSrv
import os
import network
import utime
import _thread
import gc


def init():
    bme_init()
    mpu9250_init()
    gps_init()
    datavalues_init()
    auto_connect_wifi(SSID='circuitspecialists.com', Password='')
    if (not wlan.isconnected()):
        wlan.active(False)
        global ap
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        print("AP started: ", ap.ifconfig())
    try:
        rocket_init()
        print("succesful to start")
    except:
        print("main init failed to start")
        utime.sleep(2)
        machine.reset()
        


def rocket_init():
    try:
        utime.sleep(5)
        print("http server starting")
        _thread.start_new_thread(httpserver_init, ())
    except:
        print("rocket init failed to start")
        utime.sleep(2)
        machine.reset()


def rocket_main():
    while (sensor.acceleration[0] < 1 or sensor.acceleration[1] < 1):
        pass
    while (sensor.acceleration[0] > 1 or sensor.acceleration[1] > 1 or (bme.getAltitude_ft() - data.altitude) > 4):
            data.launched = True
            try:
                data.csv.append(getDataValues())
            except:
                pass
            utime.sleep_ms(2)


def getDataValues():
    data.delta_altitude = bme.getAltitude_ft() - data.altitude
    data.x_acceleration = sensor.acceleration[0]
    data.y_acceleration = sensor.acceleration[1]
    data.pressure = bme.getPressure()

    if (data.delta_altitude >= data.max_delta_altitude):
        data.max_delta_altitude = data.delta_altitude
    if (data.x_acceleration >= data.max_x_acceleration):
        data.max_x_acceleration = data.x_acceleration
    if (data.y_acceleration >= data.max_y_acceleration):
        data.max_y_acceleration = data.y_acceleration

    gps.update()
    gps.interpret_rmc()

    datavalues = [
        data.altitude, data.delta_altitude, data.max_delta_altitude,
        data.x_acceleration, data.max_x_acceleration, data.y_acceleration,
        data.max_y_acceleration, data.pressure, gps.latitude, gps.latitude_direction,
        gps.longitude, gps.longitude_direction, gps.speed,
        gps.getformatedUTC(-7)
    ]

    return datavalues


@MicroWebSrv.route('/start')
def _httpHandlerFileGet(httpClient, httpResponse):
    gc.mem_free()
    print("Main Rocket subroutine starting")
    rocket_main()
    gc.mem_free()
    httpResponse.WriteResponseOk(
        headers=({
            'Cache-Control': 'no-cache'
        }),
        contentType='text/event-stream',
        contentCharset='UTF-8',
        content='data: {0}'.format(str(getDataValues())))

@MicroWebSrv.route('/download.csv')
def _httpHandlerFileGet(httpClient, httpResponse):
    gc.mem_free()
    httpResponse.WriteResponseOk(
        headers=({
            'Cache-Control': 'no-cache'
        }),
        contentType='text/event-stream',
        contentCharset='UTF-8',
        content='data: {0}'.format(str(data.csv)))


@MicroWebSrv.route('/sensordata')
def _httpHandlerSensorDataGet(httpClient, httpResponse):
    gc.mem_free()
    httpResponse.WriteResponseOk(
        headers=({
            'Cache-Control': 'no-cache'
        }),
        contentType='text/event-stream',
        contentCharset='UTF-8',
        content='data: {0}\n\n'.format(str(getDataValues())))


def _acceptWebSocketCallback(webSocket, httpClient):
    print("WS ACCEPT")
    webSocket.RecvTextCallback = _recvTextCallback
    webSocket.RecvBinaryCallback = _recvBinaryCallback
    webSocket.ClosedCallback = _closedCallback


def _recvTextCallback(webSocket, msg):
    print("WS RECV TEXT : %s" % msg)
    webSocket.SendText("Reply for %s" % msg)


def _recvBinaryCallback(webSocket, data):
    print("WS RECV DATA : %s" % data)


def _closedCallback(webSocket):
    print("WS CLOSED")


def httpserver_init():
    global server
    server = MicroWebSrv(webPath='www/')
    server.MaxWebSocketRecvLen = 256
    server.WebSocketThreaded = False
    server.AcceptWebSocketCallback = _acceptWebSocketCallback
    server.Start(threaded=False)


def gps_init():
    global gps
    gps = neo6mgps.NEO6MGPS(baudrate=9600)


def mpu9250_init():
    global i2c_mpu9250
    global sensor
    i2c_mpu9250 = machine.I2C(scl=machine.Pin(26), sda=machine.Pin(25))
    sensor = mpu9250.MPU9250(i2c=i2c_mpu9250)
    sensor.calibrate_MPU9250()


def bme_init():
    global i2c_bme280
    global bme
    i2c_bme280 = machine.I2C(scl=machine.Pin(33), sda=machine.Pin(32))
    bme = bme280.BME280(i2c=i2c_bme280)


def datavalues_init():
    global data
    data = DATAVALUES()
    data.altitude = bme.getAltitude_ft()


def auto_connect_wifi(SSID, Password):
    global wlan
    wlan = network.WLAN(network.STA_IF)
    if (not wlan.isconnected()):
        print('connecting to network...')
        wlan.active(True)
        wlan.connect(SSID, Password)
        for i in range(0, 3):
            if(not wlan.isconnected()):
                utime.sleep(1)
                pass
            else:
                break
    print('network config:', wlan.ifconfig())


class DATAVALUES(object):
    def __init__(self):
        self.altitude = 0.0
        self.delta_altitude = 0.0
        self.max_delta_altitude = 0.0
        self.x_acceleration = 0.0
        self.max_x_acceleration = 0.0
        self.y_acceleration = 0.0
        self.max_y_acceleration = 0.0
        self.z_acceleration = 0.0
        self.max_z_acceleration = 0.0
        self.pressure = 0.0
        self.csv = []
        self.launched = False
