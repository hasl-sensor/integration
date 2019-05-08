Home Assistant SL Sensor (HASL)
===============================

This is a platform for Home Assistant that can be used to create "Departure board" or "Traffic Situation" sensors for buses and trains in Stockholm, Sweden. You have to install it as a custom component and you need to get your own API keys from SL / Trafiklab. This is a fork of fredrikbaberg SL sensor (https://github.com/fredrikbaberg/ha-sensor-sl).

![card](https://user-images.githubusercontent.com/8133650/56198334-0a150f00-603b-11e9-9e93-92be212d7f7b.PNG)

>__NOTE__: If you are using pre 0.92 version of Home Assistant you will need to use release 1.0.3 or older from here and follow the instructions in the release files there instead (and there is some known issues with that release). The below information is for 0.92 or later versions of Home Assistant only.

## Installation

First, visit [https://www.trafiklab.se/api](https://www.trafiklab.se/api) and create a free account. They provide multiple APIs, the ones you want is ["SL Trafikinformation 4"](https://www.trafiklab.se/api/sl-realtidsinformation-4) and ["SL Störningsinformation 2"](https://www.trafiklab.se/api/sl-storningsinformation-2), optionally you can also register for ["SL Trafikläget 2"](https://www.trafiklab.se/api/sl-trafiklaget-2) to get tl2 sensors. When you have your API keys, you're ready to add the component to your Home Assistant.

Since this is a custom component it needs to manually installed. [Custom Updater](custom_updater.md) can be used to automatically update once new versions gets released. To install copy

[`hasl/__init__.py`](https://github.com/DSorlov/ha-sensor-sl/blob/hasl/custom_components/hasl/__init__.py) at `<config>/custom_components/hasl/__init__.py`  
[`hasl/sensor.py`](https://github.com/DSorlov/ha-sensor-sl/blob/hasl/custom_components/hasl/sensor.py) at `<config>/custom_components/hasl/sensor.py`  
[`hasl/manifest.json`](https://github.com/DSorlov/ha-sensor-sl/blob/hasl/custom_components/hasl/manifest.json) at `<config>/custom_components/hasl/manifest.json`

where `<config>` is your Home Assistant configuration directory.

Then add the desired configuration in config. Here is an example of a typical configuration:
 
```yaml
sensor:
- platform: hasl
  ri4key: YOUR-RI4-KEY-HERE
  si2key: YOUR-SI2-KEY-HERE
  tl2key: YOUR-OPTIONAL-TL2-KEY-HERE
  sensors:
   - friendly_name: Mölnvik
     sensor_type: comb
     siteid: 4244
     lines: 474, 480C
     direction: 1
     sensor: binary_sensor.test
   - friendly_name: Trafikstatus
     sensor_type: tl2
```
## Configuration variables
- **ri4key** (*Optional*): Your API key from Trafiklab for the Realtidsinformation 4 API (required for comb sensors)

- **si2key** (*Optional*): Your API key from Trafiklab for the Störningsinformation 2 API (required for comb sensors)

- **tl2key** (*Optional*): Your API key from Trafiklab for the Trafikläget 2 API (required for tl2 sensors)

- **sensors**: A list of all the sensors to be created. Theese can be of sensor_type `comb` or `tl2`:
  
  
## Configration variables for COMB sensors
This sensor type creates a combined departure sensor for a specific stop. You can find the ID with some help from another API , ["SL Platsuppslag](https://www.trafiklab.se/api/sl-platsuppslag/konsol)).  In the example above, site 4244 is Mölnvik. This sensor can be used with [hasl-comb-card](hasl-comb-card.md) and outputs data as described in the [sensor description](comb_sensor.md). 

 - **sensor_type: `comb`**:  Mandatory configuration for COMB sensor (must be set to `comb`)
 
 - **friendly_name**: Used as display name

 - **siteid**: The ID of the bus stop or station you want to monitor.  

 - **scan_interval** (*Optional*): Number of minutes between updates, default 5, min 5 and max 60.

 - **sensor** (*Optional*): Specify the name of a binary_sensor to determine if this sensor should be updated. If sensor is ON, or if this option is not set, update will be done.

 - **property** (*Optional*): Which property to report as sensor state. Can be one of: `min` minutes to departure (default), `time` next departure time, `deviations` number of active deviations, `refresh` if sensor is refreshing or not, `updated` when sensor data was last updated.

 - **lines** (*Optional*): A comma separated list of line numbers that you are interested in. Most likely, you only want info on the bus that you usually ride.  If omitted, all lines at the specified site id will be included.  In the example above, lines 17, 18 and 19 will be included.

 - **direction** (*Optional*): Unless your site id happens to be the end of the line, buses and trains goes in both directions.  You can enter **1** or **2**.  If omitted, both directions are included. 

 - **timewindow** (*Optional*): The number of minutes to look ahead when requesting the departure board from the api. Default 60, minimum is 5 and maximum is 60.

## Configration variables for TL2 sensors
This sensor type creates a Traffic Situation sensor and shows the all-up trafic situation in the public transportation system. This sensor can be used with [hasl-tl2-card](hasl-tl2-card.md) and outputs data as described in the [sensor description](tl2_sensor.md)

**- sensor_type: `tl2`**:  mandatory configuration for TL2 sensor and must be set to `tl2`
  
 - **friendly_name**: Used as display name

 - **scan_interval** (*Optional*): Number of minutes between updates, default 5, min 5 and max 60.

 - **sensor** (*Optional*): Specify the name of a binary_sensor to determine if this sensor should be updated. If sensor is 'on', or if this option is not set, update will be done.

 - **traffic_class** (*Optional*): A comma separated list of the types to present in the sensor if not all (`metro`,`train`,`local`,`tram`,`bus`,`fer`)
  

## API-call restrictions and optimizations

The `Bronze` level API is limited to 30 API calls per minute, 10.000 per month. With 10.000 calls per month, that allows for less than one call every 4 minute but if you are using multiple sensors this is split between them and each config sensor section can contain a separate pair of api-keys.
The calls have been optimized and are beeing locally cached for the specified freshness, if multiple sensors are using the same siteid there will still only be one call. Caching is done in a file (haslcache.json) that will be automatically created in the configuration directory.
You can also specify a binary_sensor that perhaps is turned of when no-one is at home or similar to reduce the number of calls.