Home Assistant SL Sensor (HASL)
===============================

This is a simple component for Home Assistant that can be used to create a "Departure board" for buses and trains in Stockholm, Sweden.  You have to install it as a custom component and you need to get your own API keys from SL / Trafiklab. The supporting library HASL is on PyPi(https://pypi.org/project/hasl/) but you do NOT need to download this manually. This is a fork of fredrikbaberg SL sensor (https://github.com/fredrikbaberg/ha-sensor-sl) that is now archived.

- First, visit [https://www.trafiklab.se/api](https://www.trafiklab.se/api) and create a free account. They provide multiple APIs, the ones you want is ["SL Trafikinformation 4"](https://www.trafiklab.se/api/sl-realtidsinformation-4) and ["SL Störningsinformation 2"](https://www.trafiklab.se/api/sl-storningsinformation-2). When you have your API keys, you're ready to add the component to your Home Assistant. Since this is a custom component, you need to add it manually to your config directory.

- Create a folder named **custom_components** under your Home Assistant **config** folder. 

- Create a folder named **sl** under the **custom_components** folder.

- Download sensor.py from here and put it in the **sl** folder.

- Edit your configuration.yaml file and add the component

```yaml
# Example configuration.yaml entry
- platform: sl
  ri4key: YOUR-RI4-KEY-HERE
  si2key: YOUR-SI2-KEY-HERE
  siteid: 4244
  friendly_name: Mölnvik
  lines: 474, 480C
  direction: 1
  sensor: binary_sensor.test
```


**Configuration variables**

- ri4key: Your API key from Trafiklab for the Realtidsinformation 4 API

- si2key: Your API key from Trafiklab for the Störningsinformation 2 API

- siteid: The ID of the bus stop or station you want to monitor.  You can find the ID with some help from another API, **sl-platsuppslag**.  In the example above, site 4244 is Mölnvik. (Console for the API can be found on https://www.trafiklab.se/api/sl-platsuppslag/konsol)

- lines: (optional) A comma separated list of line numbers that you are interested in. Most likely, you only want info on the bus that you usually ride.  If omitted, all lines at the specified site id will be included.  In the example above, lines 17, 18 and 19 will be included.

- direction: (optional) Unless your site id happens to be the end of the line, buses and trains goes in both directions.  You can enter **1** or **2**.  If omitted, both directions are included. 

- sensor: (optional) Sensor to determine if status should be updated. If sensor is 'on', or if this option is not set, update will be done.

- scan_interval: (optional) Number of minutes between updates, default 5, min 5 and max 60.

- timewindow: (optionl) The number of minutes to look ahead when requesting the departure board from the api. Default 30, min 5 and max 60.

- sensor: (optional) Specify the name of a binary_sensor to determine if this sensor should be updated. If sensor is 'on', or if this option is not set, update will be done.

- friendly_name: (optional) Used as display name, if not specifed the name is used by default

**Sensor value**

The sensor value is the number of minutes to the next departure.  There are also a number of attributes that can help you with filtering or whatever you need:

```
unit_of_measurement: min
icon: mdi:subway
friendly_name: Mölnvik
attribution: Stockholms Lokaltrafik
next_departure_minutes: 10
next_departure_expected: 19:10:00
last_refresh: 2018-11-16 19:08:40
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

**Lovelace card**

To display data using Lovelace, you can try the included card.
Present departure times from custom component SL-sensor in a card. 
Thanks to [@dimmanramone](https://github.com/dimmanramone) for pimping the card!

![card](https://user-images.githubusercontent.com/8133650/56198334-0a150f00-603b-11e9-9e93-92be212d7f7b.PNG)

Install it throgh copying the file `www/sl-card.js` into `config_dir/www/`, and use the following in your ui-lovelace.yaml file:
```
resources:
  - url: /local/sl-card.js
    type: js
```
and use the card throgh
```
cards:
  - type: "custom:sl-card"
    header: false
    departures: true
    deviations: true
    timeleft: false
    updated: true
    name: Departures
    adjust_time: false
    hide_departed: false
    language: en-EN
    entities:
      - sensor.hasl_name
```
- header: Render headers in the such as "line", "destination" and "time"

- departures: Render departure section

- deviations: Render deviation section

- updated: Render the last updated time section

- timeleft: Show as SL real time with minutes instead of time

- adjust_time: Calculate time left adjusted to last update (used in conjunction with timeleft)

- hide_departed: This can hide already departured

- language: The texts will be rendered in this language (sv-SE or en-EN)

- name: If specified it will not render titles per entitiy in the card, but rather have this as the card name. If not speficied it will render each sensors name
