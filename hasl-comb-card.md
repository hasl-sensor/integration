SL Combination Sensor Lovelace Card
===============================
This describes the sensor card for use with SL Comb Sensor as described in the [Home Assistant SL Sensor readme](README.md) To display data using Lovelace, you can try the included card.
Present departure times from custom component SL-sensor in a card. Huge thanks to [@dimmanramone](https://github.com/dimmanramone) for pimping the card!

![card](https://user-images.githubusercontent.com/8133650/56198334-0a150f00-603b-11e9-9e93-92be212d7f7b.PNG)

## Installation
For updating instructions see [Custom Updater](custom_updater.md).

Copy [`hasl/www/hasl-comb-card.js`](https://github.com/DSorlov/ha-sensor-sl/blob/hasl/www/hasl-comb-card.js) to `<config>/www/hasl-comb-card.js`  

 and use the following in your ui-lovelace.yaml file:
 
```yaml
resources:
  - url: /local/hasl-comb-card.js
    type: js
```

and use the card throgh this example:

```yaml
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

## Configration variables 
- **header**: Render headers in the such as "line", "destination" and "time"

- **departures** (*Optional*): Render departure section, default `false`

- **deviations** (*Optional*): Render deviation section, default `false`

- **updated** (*Optional*): Render the last updated time section

- **timeleft** (*Optional*): Show as SL real time with minutes instead of time. If using **adjust_times** then this must be specified.

- **adjust_times** (*Optional*): Calculate time left adjusted to last update (used in conjunction with timeleft)

- **hide_departed** (*Optional*): This can hide already departured transports

- **language** (*Optional*): The texts will be rendered in this language. Can be one of `sv-SE` or `en-EN`

- **name** (*Optional*): If specified it will not render titles per entitiy in the card, but rather have this as the card name. If not speficied it will render each sensors name

- **max_departures** (*Optional*): Max departures to show, default to all.
  
- **max_deviations** (*Optional*): Max deviations to show, defaults to all.

- **compact** (*Optional*): Compact style of the card. Default value is `true`
