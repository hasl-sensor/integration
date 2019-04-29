Home Assistant SL Sensor (HASL)
===============================

This is a platform for Home Assistant that can be used to create "Departure board" or "Traffic Situation" sensors for buses and trains in Stockholm, Sweden. You have to install it as a custom component and you need to get your own API keys from SL / Trafiklab. The supporting library HASL is on PyPi(https://pypi.org/project/hasl/) but you do NOT need to download this manually. This is a fork of fredrikbaberg SL sensor (https://github.com/fredrikbaberg/ha-sensor-sl).

**If you are using pre 0.92 version of Home Assistant you will need to use release 1.0.3 or older from here and follow the instructions in the release files there instead (and there is some known issues with that release). The below information is for 0.92 or later versions of Home Assistant only.**

- First, visit [https://www.trafiklab.se/api](https://www.trafiklab.se/api) and create a free account. They provide multiple APIs, the ones you want is ["SL Trafikinformation 4"](https://www.trafiklab.se/api/sl-realtidsinformation-4) and ["SL Störningsinformation 2"](https://www.trafiklab.se/api/sl-storningsinformation-2), optionally you can also register for ["SL Trafikläget 2"](https://www.trafiklab.se/api/sl-trafiklaget-2) to get tl2 sensors. When you have your API keys, you're ready to add the component to your Home Assistant. Since this is a custom component, you need to add it manually to your config directory.

- Create a folder named **custom_components** under your Home Assistant **config** folder. 

- Create a folder named **hasl** under the **custom_components** folder.

- Download content from the **custom_components/hasl** folder from here and put it in the **custom_components/hasl** folder in your server.

- Edit your configuration.yaml file and add the component

```yaml
# Example configuration.yaml entry
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


**Configuration variables**

- ri4key: (optional) Your API key from Trafiklab for the Realtidsinformation 4 API (required for comb sensor)

- si2key: (optional) Your API key from Trafiklab for the Störningsinformation 2 API (required for comb sensor)

- tl2key: (optional) Your API key from Trafiklab for the Trafikläget 2 API (required for tl2 sensor)

- sensors: A list of all the sensors to be created. Theese can be of sensor_type 'comb' or 'tl2':
  
  **- sensor_type: 'comb'**  -- this sensor type creates a combined departure sensor
  
   - friendly_name: Used as display name

   - siteid: The ID of the bus stop or station you want to monitor.  You can find the ID with some help from another API, **sl-platsuppslag**.  In the example above, site 4244 is Mölnvik. (Console for the API can be found on https://www.trafiklab.se/api/sl-platsuppslag/konsol)

   - scan_interval: (optional) Number of minutes between updates, default 5, min 5 and max 60.

   - sensor: (optional) Specify the name of a binary_sensor to determine if this sensor should be updated. If sensor is 'on', or if this option is not set, update will be done.

   - property: (optional) Which property to report as sensor state ['min'= minutes to departure (default), 'time'= next departure time, 'deviations'= number of active deviations, 'refresh'= if sensor is refreshing or not, 'updated'=when sensor data was last updated]

   - lines: (optional) A comma separated list of line numbers that you are interested in. Most likely, you only want info on the bus that you usually ride.  If omitted, all lines at the specified site id will be included.  In the example above, lines 17, 18 and 19 will be included.

   - direction: (optional) Unless your site id happens to be the end of the line, buses and trains goes in both directions.  You can enter **1** or **2**.  If omitted, both directions are included. 

   - timewindow: (optionl) The number of minutes to look ahead when requesting the departure board from the api. Default 30, min 5 and max 60.

   - traffic_class: (optional) A comma separated list of the types to present in the sensor if not all (metro,train,local,tram,bus,fer)

  **- sensor_type: 'tl2'**  -- this sensor type creates a tl2 sensor
  
   - friendly_name: Used as display name

   - scan_interval: (optional) Number of minutes between updates, default 5, min 5 and max 60.

   - sensor: (optional) Specify the name of a binary_sensor to determine if this sensor should be updated. If sensor is 'on', or if this option is not set, update will be done.

   - traffic_class: (optional) A comma separated list of the types to present in the sensor if not all (metro,train,local,tram,bus,fer)
   
**COMB Sensor value**

The sensor value is the number of minutes to the next departure (or if something else is configured that will be used instead).  There are also a large number of attributes that can help you with filtering or whatever you need:

```
friendly_name: Mölnvik
unit_of_measurement: min
icon: mdi:subway
attribution: Stockholms Lokaltrafik
last_refresh: 2018-11-16 19:08:40
next_departure_minutes: 10
next_departure_time: 19:18:40
deviation_count: 1
refresh_enabled: on
departure_board: [{
 line: 474
 direction: 1
 departure: 10 min
 destination: Slussen
 diff: 10
 type: Buses
 icon: mdi:bus
}]
deviances: [{
 updated: 2018-11-16T15:59:40.063+01:00
 title: Inställd avgång
 fromDate: 2018-11-16T15:59:40.663
 toDate: 2018-11-17T00:00:00
 details: "Mölnvik kl 16:17 till Slussen är inställd pga framkomlighetsproblem - köer."
 sortOrder: 1
}]
```

**TL2 Sensor value**

The sensor value is the last update of the sensor.  There are also a number of attributes that can help you with filtering:

```
metro_status: Good
metro_icon: mdi:check-bold
train_status: Good
train_icon: mdi:check-bold
local_status: Good
local_icon: mdi:check-bold
tram_status: Minor
tram_icon: mdi:clock-outline
bus_status: Good
bus_icon: mdi:check-bold
fer_status: Good
fer_icon: mdi:check-bold
attribution: Stockholms Lokaltrafik
last_updated: 2019-04-26 19:30:27
friendly_name: SL Trafikstatus
icon: mdi:train-car
```

**API-call restrictions**

The `Bronze` level API is limited to 30 API calls per minute, 10.000 per month.
For a private project, `Silver` level does not seem possible.
With 10.000 calls per month, that allows for less than one call every 4 minute.
That is why it is better to specify a binary_sensor that perhaps is turned of when no-one is at home or similar.


**Automatic updates**

For update check of this sensor, add the following to your configuration.yaml. For more information, see [[custom_updater](https://github.com/custom-components/custom_updater/wiki/Installation)]

```
custom_updater:
  track:
    - components
	- cards
  component_urls:
    - https://raw.githubusercontent.com/DSorlov/ha-sensor-sl/hasl/custom_updater.json
  card_urls:
    - https://raw.githubusercontent.com/DSorlov/ha-sensor-sl/hasl/custom_cards.json
```

**Lovelace card (for Departure Sensor, hasl-comb-card.js)**

To display data using Lovelace, you can try the included card.
Present departure times from custom component SL-sensor in a card. 
Thanks to [@dimmanramone](https://github.com/dimmanramone) for pimping the card!

![card](https://user-images.githubusercontent.com/8133650/56198334-0a150f00-603b-11e9-9e93-92be212d7f7b.PNG)

Install it throgh copying the file `www/hasl-comb-card.js` into `config_dir/www/`, and use the following in your ui-lovelace.yaml file:
```
resources:
  - url: /local/hasl-comb-card.js
    type: js
```
and use the card throgh
```
cards:
  - type: "custom:hasl-comb-card"
    header: false
    departures: true
    deviations: true
    timeleft: false
    updated: true
    name: Departures
    adjust_times: false
    hide_departed: false
    language: en-EN
    entities:
      - sensor.hasl_name
```
- header: Render headers in the such as "line", "destination" and "time"

- departures: Render departure section

- deviations: Render deviation section

- updated: Render the last updated time section

- timeleft: Show as SL real time with minutes instead of time (over 60 mins left also shows time)

   - adjust_times: Calculate time left adjusted to last update (used in conjunction with timeleft)

   - always_show_time: Always show "2 min (12:22)" instead of just "2 min" for sub hour departures (used in conjunction with timeleft)

- hide_departed: This can hide already departured

- language: The texts will be rendered in this language (sv-SE or en-EN)

- name: If specified it will not render titles per entitiy in the card, but rather have this as the card name. If not speficied it will render each sensors name
