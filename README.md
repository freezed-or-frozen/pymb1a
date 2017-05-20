# pymb1a
Python class to communicate with Xiaomi Mi band 1A fitness tracker.
Should works on Python 3.4 under Linux OS.


## Requirements
This class use bluepy to handle BLuetooth Low Energy communication. Have a look at https://github.com/IanHarvey/bluepy
```
pip3 install bluepy
```

## Installation
Download the main class file and add it to your project

## Usage
Import the class
```
import mi_band_1a
```

Instanciate with bluetooth address of the Mi Band device
```
mb1a = MiBand1A("C8:0F:10:01:02:03")
```

Scan and connect to the device
```
mb1a.scan_and_connect()
```

Get useful services and characteristics
```
mb1a.get_services_and_characteristics()
```

Subscribe to useful notifications
```
mb1a.subscribe_to_notifications()
```

Read some public informations
```
print("   + device_info : ", mb1a.read_device_info() )
print("   + date_time : ", mb1a.read_date_time() )
print("   + battery : ", mb1a.read_battery() )
print("   + realtime_steps : ", mb1a.read_realtime_steps() )
```

Authenticate in order to read private informations (activity data and sensor data)
```
print("   + authenticate success : ", mb1a.authenticate() )
```

Fetch activity data
```
print("   + activity data steps recorded : ", mb1a.fetch_activity_data("dump_activity_data.csv") )
```

Record about 300 sensor data samples in a CSV file (a little bit more actually)
```
mb1a.record_sensor_data("dump_sensor_data.csv", 300)
```

Finally disconnect to the device
```
mb1a.disconnect()
```


## Changelog
Release 0.1.0
- first release
- can read and record in a CSV file raw value from accelerometer
- can read and count steps done in activity data recorded in the device
