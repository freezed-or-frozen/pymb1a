"""
@brief Python class to communicate with the Xiaomi Mi Band 1A
@author David SALLE
@date 10/05/2017
@version 0.1.0
@licence GPLv3
"""

# Standard librairies
import time
import math
import datetime

# Other library (need a custom installation: pip3 install bluepy)
import bluepy


class MiBand1A(bluepy.btle.DefaultDelegate):
    """MiBand1A class
    """
    def __init__(self, gender, age, height, weight, alias, which_hand, keep_data):
        """Constructor method to initialise everything useful
        @param {MiBand1A} self
        @param {string} alias user name (8 characters max)
        @param {integer} gender (0=female, 1=man, 2=other)
        @param {integer} age
        @param {integer} height in cm (e.g.: 175)
        @param {integer} weight in kg (e.g.: 75)
        @param {string} alias user name (ex: "jbegood")
        @param {integer} which_hand (left=0, right=1)
        @return None
        """
        # Call the super class constructor
        bluepy.btle.DefaultDelegate.__init__(self)

        # Some initializations
        self.gender = gender
        self.age = age
        self.height = height
        self.weight = weight
        self.alias = alias
        self.which_hand = which_hand
        self.keep_data = keep_data

        self.bluetooth_address = None
        self.device = None
        self.sensor_data_csv_file = None
        self.activity_data_csv_file = None
        self.gravity = 9.81
        self.scale_factor = 1000
        self.authentication_ended = False
        self.upload_in_progress = False
        self.activity_data = []
        self.ack_messages = []
        self.data_block_datak_counter = 0


    def handleDiscovery(self, dev, is_new_dev, is_new_data):
        """Method to handle discovery of new BLE devices
        @param {MiBand1A} self
        @param {ScanEntry} dev
        @param {boolean} is_new_dev
        @param {boolean} isNewData
        @return None
        """
        if is_new_dev:
            print("   + Discovered device : address=%s rssi=%d dBm" % (dev.addr, dev.rssi) )
        elif is_new_data:
            print("   + Received new data from", dev.addr)


    def scan_and_connect(self, timeout, bluetooth_addresses, rssi_threshold):
        """Method to scan and connect to a chosen and close  BLE device
        @param {MiBand1A} self
        @param {float} timeout
        @param {list} bluetooth_addresses of Mi Band wrist
        @param {integer} rssi_threshold
        @return {string} bluetooth_address of the connected device or None
        """
        # Start scanning for devices to connect to
        scanner = bluepy.btle.Scanner().withDelegate(self)
        devices = scanner.scan(timeout)

        # Is a Mi Band inside the ScanEntry list after scanning
        for dev in devices:
            for bluetooth_address in bluetooth_addresses:
                if dev.addr == bluetooth_address and dev.rssi > rssi_threshold:
                    print("   + Found a Mi Band 1A in the wish list, try to connect")
                    self.bluetooth_address = dev.addr
                    self.device = bluepy.btle.Peripheral(self.bluetooth_address)
                    self.device.setDelegate( self )
                    return True
        return False


    def disconnect(self):
        """Method to disconnect the device
        @param {MiBand1A} self
        @return None
        """
        # Disconect the device (if already connected)
        if self.device is not None:
            self.device.disconnect()


    def get_services_and_characteristics(self):
        """Method to get services and charactestics needed to play with the Mi Band
        @param {MiBand1A} self
        @return None
        """
        # Get useful services
        self.mili_service = self.device.getServiceByUUID("0000fee0-0000-1000-8000-00805f9b34fb")

        # Get useful characteristics
        self.device_info_characteristic =       self.mili_service.getCharacteristics("0000ff01-0000-1000-8000-00805f9b34fb")[0]
        self.device_name_characteristic =       self.mili_service.getCharacteristics("0000ff02-0000-1000-8000-00805f9b34fb")[0]
        self.notification_characteristic =      self.mili_service.getCharacteristics("0000ff03-0000-1000-8000-00805f9b34fb")[0]
        self.user_info_characteristic =         self.mili_service.getCharacteristics("0000ff04-0000-1000-8000-00805f9b34fb")[0]
        self.control_point_characteristic =     self.mili_service.getCharacteristics("0000ff05-0000-1000-8000-00805f9b34fb")[0]
        self.realtime_steps_characteristic =    self.mili_service.getCharacteristics("0000ff06-0000-1000-8000-00805f9b34fb")[0]
        self.activity_data_characteristic =     self.mili_service.getCharacteristics("0000ff07-0000-1000-8000-00805f9b34fb")[0]
        self.firmware_data_characteristic =     self.mili_service.getCharacteristics("0000ff08-0000-1000-8000-00805f9b34fb")[0]
        self.le_params_characteristic =         self.mili_service.getCharacteristics("0000ff09-0000-1000-8000-00805f9b34fb")[0]
        self.date_time_characteristic =         self.mili_service.getCharacteristics("0000ff0a-0000-1000-8000-00805f9b34fb")[0]
        self.statistics_characteristic =        self.mili_service.getCharacteristics("0000ff0b-0000-1000-8000-00805f9b34fb")[0]
        self.battery_characteristic =           self.mili_service.getCharacteristics("0000ff0c-0000-1000-8000-00805f9b34fb")[0]
        self.test_characteristic =              self.mili_service.getCharacteristics("0000ff0d-0000-1000-8000-00805f9b34fb")[0]
        self.sensor_data_characteristic =       self.mili_service.getCharacteristics("0000ff0e-0000-1000-8000-00805f9b34fb")[0]


    def subscribe_to_notifications(self):
        """Method to subscribe to all interesting notification characteristics
        @param {MiBand1A} self
        @return None
        """
        subscribe_command = bytes([0x01, 0x00])

        notification_handle = self.notification_characteristic.getHandle() + 1
        self.device.writeCharacteristic(notification_handle, subscribe_command, withResponse=True)

        activity_data_handle = self.activity_data_characteristic.getHandle() + 1
        self.device.writeCharacteristic(activity_data_handle, subscribe_command, withResponse=True)

        sensor_data_handle = self.sensor_data_characteristic.getHandle() + 1
        self.device.writeCharacteristic(sensor_data_handle, subscribe_command, withResponse=True)


    def authenticate(self):
        """Method to authenticate user
        @param {MiBand1A} self
        @return {boolean} success or fail
        """
        data = bytes([0x27, 0x4e, 0x92, 0x06, 0x02, 0x19, 0xaf, 0x46, 0x00, 0x05, 0x00, 0x74, 0x65, 0x73, 0x74, 0x79, 0x00, 0x00, 0x00, 0x16])
        self.user_info_characteristic.write(data, True)
        timeout_counter = 0
        while self.authentication_ended == False and timeout_counter < 100:
            time.sleep(0.1)
            timeout_counter += 1
        if timeout_counter < 100:
            return True
        else:
            return False


    def read_device_info(self):
        """Method to read the device information
        @param {MiBand1A} self
        @return {dict} device_information
        """
        # TODO: decode data
        device_information = {}
        data = self.device_info_characteristic.read()
        return device_information


    def read_date_time(self):
        """Method to read date time in the wrist
        @param {MiBand1A} self
        @return {dict} date_time
        """
        # Read date time characteristics as bytes
        data = self.date_time_characteristic.read()
        #print("DEBUG => ", data)

        # Analyse and decode bytes
        date_time = {}
        if len(data) == 7:
            year = data[1] + 2000
            month = data[2] + 1
            day = data[3]
            hour = data[4]
            minute = data[5]
            second = data[6]

            # Package all as a dictionary
            date_time = {"year":year, "month": month, "day": day, "hour": hour, "minute": minute, "second":second}
        return date_time


    def read_battery(self):
        """Method to read battery informations
        @param {MiBand1A} self
        @return {dict} battery_informations
        """
        # Read date time characteristics as bytes
        data = self.battery_characteristic.read()
        #print("DEBUG => ", data)

        # Analyse and decode bytes
        battery_informations = {}
        if len(data) == 10:
            level = data[0]
            year = data[1] + 2000
            month = data[2] + 1
            day = data[3]
            hour = data[4]
            minute = data[5]
            second = data[6]
            cycles = 0xffff & (0xff & data[7] | (0xff & data[8]) << 8)
            status = data[9]

            # Package all as a dictionary
            battery_informations = {"level": level, "year":year, "month": month, "day": day, "hour": hour, "minute": minute, "second":second, "cycles": cycles, "status": status}

        return battery_informations


    def read_realtime_steps(self):
        """Method to read the realtime steps. Warning, Mi Band delete value everyday
        @param {MiBand1A} self
        @return {integer} realtime steps
        """
        data = self.realtime_steps_characteristic.read()
        return int.from_bytes(data, byteorder='little')


    def record_sensor_data(self, csv_file_name, samples):
        """Method to read and record some sensor data in a CSV file
        @param {MiBand1A} self
        @return None

        Sensor data means raw x-axis, y-axis and z-axis values
        """
        # Open CSV file
        self.sensor_data_csv_file = open(csv_file_name, "w")
        self.sensor_data_csv_file.write("x-axis;y-axis;z-axis\n")

        # Enable live sensor data
        on_command = bytes([0x12, 0x01])
        self.control_point_characteristic.write(on_command, True)

        # Loop waiting for sensor data
        for i in range(0, samples):
            mb1a.wait_for_notifications(1.0)

        # Disable live sensor data
        off_command = bytes([0x12, 0x00])
        self.control_point_characteristic.write(off_command, True)

        # Close CSV file
        self.sensor_data_csv_file.close()


    def fetch_activity_data(self, csv_file_name=None):
        """Method to fetch activity data recorded in the Mi Band
        @param {MiBand1A} self
        @return {integer} steps done
        """
        # Don't know what it is
        magic_command = bytes([0x01, 0x00])
        magic_handle = self.realtime_steps_characteristic.getHandle() + 1
        self.device.writeCharacteristic(magic_handle, magic_command, withResponse=True)

        # Send the FETCH command
        fetch_command = bytes([0x06])
        self.control_point_characteristic.write(fetch_command, True)

        # Wait for notification
        self.upload_in_progress = True
        while self.upload_in_progress == True:
            mb1a.wait_for_notifications(1.0)

        # Analyse activity data and return steps done
        return self.analyse_activity_data(csv_file_name)


    def wait_for_notifications(self, delay):
        """Method to wait for notifications to come
        @param {MiBand1A} self
        @param {float} delay to wait in seconds
        @return None
        """
        return self.device.waitForNotifications(delay)


    def prepare_ack_message(self, data):
        """Method to prepare ack messages to delete or keep data in the Mi Band
        @param {MiBand1A} self
        @param {bytes} header data
        @return None
        """
        # Prepare ack message
        self.data_block_datak_counter += 1
        year = data[1]
        month = data[2]
        day = data[3]
        hour = data[4]
        minute = data[5]
        second = data[6]
        bytes_transferred = ((data[10] * 256) + data[9]) * 3
        if self.keep_data == True:
            checksum_msb = (~bytes_transferred) & 0xff            # Checksum formula if we do not want to delete data on wrist
            checksum_lsb = 0xff & (~bytes_transferred >> 8)
        else:
            checksum_msb = bytes_transferred & 0xff               # Checksum if we want to delete data on wrist
            checksum_lsb = 0xff & (bytes_transferred >> 8)
        ack_message = bytes([0x0a, year, month, day, hour, minute, second, checksum_msb, checksum_lsb])

        if self.data_block_datak_counter > 1:
            self.ack_messages.append(ack_message)


    def analyse_activity_data(self, csv_file_name):
        """Method to analyse and decode activity data.
        @param {MiBand1A} self
        @param {string} csv_file_name
        @return {integer} steps done
        """
        global_cursor = 0
        local_cursor = 0
        next_header = 0
        temp_header_data = []
        temp_block_data = []
        steps_counter = 0
        minutes_counter = 0
        end_of_analyse = False
        start_timestamp = 0

        # Open CSV file
        if csv_file_name is not None:
            activity_data_csv_file = open(csv_file_name, "w")
            activity_data_csv_file.write("timestamp;activity_type;intensity;steps\n")

        while end_of_analyse == False:
            # Analyse header block
            temp_header_data = self.activity_data[global_cursor:global_cursor+11]
            year = temp_header_data[1] + 2000
            month = temp_header_data[2] + 1
            day = temp_header_data[3]
            hour = temp_header_data[4]
            minute = temp_header_data[5]
            second = temp_header_data[6]
            start_date = datetime.datetime(year, month, day, hour, minute, second)
            start_timestamp = int((time.mktime(start_date.timetuple()) + start_date.microsecond/1000000.0)*1000)
            data_until_next_header = ((temp_header_data[10] * 256) + temp_header_data[9]) * 3
            global_cursor += 11

            if data_until_next_header == 0:
                end_of_analyse = True

            # Analyse data block
            local_cursor = 0
            while local_cursor < data_until_next_header:
                # Slice in 3 bytes blocks
                temp_block_data = self.activity_data[global_cursor:global_cursor+3]
                global_cursor += 3
                local_cursor += 3
                minutes_counter += 1
                activity_data_csv_file.write("%d;%d;%d;%d\n" % (start_timestamp + (minutes_counter * 60), temp_block_data[0], temp_block_data[1], temp_block_data[2]) )
                #print("%d | %d | %d | %d" % (start_timestamp + (minutes_counter * 60), temp_block_data[0], temp_block_data[1], temp_block_data[2]) )
                if temp_block_data[2] > 0:
                    steps_counter += temp_block_data[2]

        # Close CSV file if open before
        if activity_data_csv_file is not None:
            activity_data_csv_file.close()

        return steps_counter


    def analyse_raw_data(self, data):
        """Method to analyse and decode raw data from accelerometer (sensor data)
        @param {MiBand1A} self
        @param {bytes} data
        @return {float} acceleration in m^s-2
        """
        # How to decode sensor data : https://github.com/Freeyourgadget/Gadgetbridge/issues/63
        counter = (data[1] * 256) + data[0]
        for idx in range(0, (len(data)-2) // 6):
            step = idx * 6
            x_raw_value = ((data[step+3] * 256) + data[step+2]) & 0x0fff
            x_sign = (data[step+3] & 0x30) >> 4
            x_type = (data[step+3] & 0xc0) >> 6
            if x_sign == 0:
                x_acc_value = (x_raw_value & 0x7ff)
            else:
                x_acc_value = ~((x_raw_value & 0x7ff) - 1)
            x_acc_value = (x_acc_value / self.scale_factor) * self.gravity
            #print("x_type=%d   x_sign=%d   x_raw_value=%d   x_acc_value=%f" % (x_type, x_sign, x_raw_value, x_acc_value))

            y_raw_value = ((data[step+5] * 256) + data[step+4]) & 0x0fff
            y_sign = (data[step+5] & 0x30) >> 4
            y_type = (data[step+5] & 0xc0) >> 6
            if y_sign == 0:
                y_acc_value = (y_raw_value & 0x7ff)
            else:
                y_acc_value = ~((y_raw_value & 0x7ff) - 1)
            y_acc_value = (y_acc_value / self.scale_factor) * self.gravity
            #print("y_type=%d   y_sign=%d   y_raw_value=%d   y_acc_value=%f" % (y_type, y_sign, y_raw_value, y_acc_value))

            z_raw_value = ((data[step+7] * 256) + data[step+6]) & 0x0fff
            z_sign = (data[step+7] & 0x30) >> 4
            z_type = (data[step+7] & 0xc0) >> 6
            if z_sign == 0:
                z_acc_value = (z_raw_value & 0x7ff)
            else:
                z_acc_value = ~((z_raw_value & 0x7ff) - 1)
            z_acc_value = (z_acc_value / self.scale_factor) * self.gravity
            #print("z_type=%d   z_sign=%d   z_raw_value=%d   z_acc_value=%f" % (z_type, z_sign, z_raw_value, z_acc_value))

            #millis = int(round(time.time() * 1000))
            #print("%d | %f | %f | %f " % (x_raw_value, x_acc_value, y_acc_value, z_acc_value))
            if self.sensor_data_csv_file is not None:
                self.sensor_data_csv_file.write("%f;%f;%f\n" % (x_acc_value, y_acc_value, z_acc_value))


    def handleNotification(self, handle, data):
        """Method overloaded from mother class to handle notifications
        @param {MiBand1A} self
        @param {integer} BLE handle of the notification characteristic
        @param {bytes} data
        @return None
        """

        # DEBUG
        """
        print(handle, end=" : ")
        for b in data:
            print(b, end=" ")
        print("")
        """

        # Handling notifications
        if handle == 22:
            if data[0] == 0x05:
                print("   + Authentication ok")
                self.authentication_ended = True
            elif data[0] == 0x06:
                print("   + Authentication failed")
                self.authentication_ended = True
            else:
                print("   + Unknown notification")


        # Handling activity data
        if handle == 32:
            for b in data:
                self.activity_data.append(b)

            if len(data) == 11 and data[0] == 0x01 and data[1] == 0x11:     # It is an header

                # Compute data to transfer
                bytes_transferred = ((data[10] * 256) + data[9]) * 3

                # Prepare ack message to delete or keep data in the device
                self.prepare_ack_message(data)

                # If it is the last header, it means that all data were transfered
                if bytes_transferred == 0:
                    for an_ack_message in self.ack_messages:
                        self.control_point_characteristic.write(an_ack_message, True)
                    #print(self.activity_data)
                    self.upload_in_progress = False


        # Handling sensor data
        if handle == 49:
            self.analyse_raw_data(data)



if __name__ == "__main__":
    # Header message
    print("\n***********************")
    print("*** MiBand1A v0.1.0 ***")
    print("***********************\n")

    try:
        print(" => Instanciate object")
        mb1a = MiBand1A(gender=2, age=25, height=175, weight=70, alias="testy", which_hand=0, keep_data=True)

        print(" => Scan for 5 and try to connect to a Xiaomi Mi Band 1A")
        if mb1a.scan_and_connect(5.0, ["c8:0f:10:76:8f:85", "c8:0f:10:76:8f:79"], -80) == True:

            print(" => Get services and characteristics")
            mb1a.get_services_and_characteristics()

            print(" => Subscribe to notifications")
            mb1a.subscribe_to_notifications()

            print(" => Read device info")
            print("   + device_info : ", mb1a.read_device_info() )

            print(" => Authenticate")
            print("   + authenticate success : ", mb1a.authenticate() )

            print(" => Read date time")
            print("   + date_time : ", mb1a.read_date_time() )

            print(" => Read device info")
            print("   + device_info : ", mb1a.read_device_info() )

            print(" => Read battery")
            print("   + battery : ", mb1a.read_battery() )

            print(" => Read realtime steps")
            print("   + realtime_steps : ", mb1a.read_realtime_steps() )

            print(" => Fetch activity data")
            print("   + activity data steps recorded : ", mb1a.fetch_activity_data("dump_activity_data.csv") )

            time.sleep(1)

            #print(" => Record sensor data")
            #mb1a.record_sensor_data("dump_sensor_data.csv", 300)

    finally:
        print(" => Disconnect")
        mb1a.disconnect()
