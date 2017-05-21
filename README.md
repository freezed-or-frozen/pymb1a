# pymb1a
Python class to communicate with Xiaomi Mi band 1A fitness tracker.
Should works on Python 3.4 under Linux OS.


## Requirements
This class use bluepy to handle Bluetooth Low Energy communication. Have a look at https://github.com/IanHarvey/bluepy
```
pip3 install bluepy
```


## Installation
Download the main class file and add it to your project


## Usage
Import the class
```python
import mi_band_1a
```

Instanciate with a few informations
```python
mb1a = MiBand1A(gender=2, age=25, height=175, weight=70, alias="jbegood", which_hand=0, keep_data=True)
```

Scan with a 5s timeout all good device close enought with a -80 dBm RSSI threshold
```python
if mb1a.scan_and_connect(5.0, ["c8:0f:10:01:02:03", "c8:0f:10:04:05:06"], -80) == True:
    # do the rest (get characteristics, subscribe notifications, read/write informations, authenticate, activity/sensor data...)
```

Get useful services and characteristics
```python
mb1a.get_services_and_characteristics()
```

Subscribe to useful notifications
```python
mb1a.subscribe_to_notifications()
```

Read some public informations
```python
print("   + device_info : ", mb1a.read_device_info() )
print("   + date_time : ", mb1a.read_date_time() )
print("   + battery : ", mb1a.read_battery() )
print("   + realtime_steps : ", mb1a.read_realtime_steps() )
```

Authenticate in order to read private informations (activity data and sensor data)
```python
print("   + authenticate success : ", mb1a.authenticate() )
```

Fetch activity data, decode it to read the steps recorded inside
```python
print("   + activity data steps recorded : ", mb1a.fetch_activity_data("dump_activity_data.csv") )
```

Record about 300 sensor data samples in a CSV file (a little bit more actually)
```python
mb1a.record_sensor_data("dump_sensor_data.csv", 300)
```

Finally disconnect to the device
```python
mb1a.disconnect()
```


## To do list
Basic informations roadmap :
- read basic informations
  - ~~battery~~
  - ~~realtime steps~~
  - date time
  - device informations
  - device name
  - goal
- write basic informations
  - date time
  - device name
  - goal
- ~~vibrate the wrist~~
- ~~light on/off leds~~

Private informations roadmap :
- authenticate to access private data (activity data and sensor data)

Sensor data roadmap :
- ~~read sensor data (accelerometer raw value)~~
- ~~analyse and record sensor data (accelerometer raw value) in a CSV file~~

Activity data roadmap :
- ~~read activity data (steps, sleep) recorded in the device~~
- ~~analyse and count steps contained in activity data~~
- analyse sleep informations contained in activity data
- ~~analyse and record sensor data (accelerometer raw value) in a CSV file~~

Other roadmap
- create a pip package
- write documentation


## Changelog
Release 0.1.0
- first release
- read basic informations like battery, realtime steps
- can read and record in a CSV file raw value from accelerometer
- can read and count steps done in activity data recorded in the device
