SL TL2 Sensor Lovelace Card
===============================
This describes the sensor card for use with SL TL2 Sensor as described in the [Home Assistant SL Sensor readme](README.md) To display data using Lovelace, you can try the included card.

## Installation
For updating instructions see [Custom Updater](custom_updater.md).

Copy [`hasl/www/hasl-tl2-card.js`](https://github.com/DSorlov/ha-sensor-sl/blob/hasl/www/hasl-tl2-card.js) to `<config>/www/hasl-tl2-card.js`  

 and use the following in your ui-lovelace.yaml file:
 
```yaml
resources:
  - url: /local/hasl-tl2-card.js
    type: js
```

and use the card throgh this example:

```yaml
cards:
  - type: custom:hasl-tl2-card
        name: Traffic Status
        language: en-EN
        show_time: false
        hide_events: false
        show_only_disturbances: false
        entities:
          - sensor.traffic_status
```

## Configration variables 
- **name** (*Optional*): If specified it will not render titles per entitiy in the card, but rather have this as the card name. If not speficied it will render each sensors name

- **language** (*Optional*): The texts will be rendered in this language. Can be one of `sv-SE` or `en-EN`-

- **show_time**: Render the time beside the name of the card

- **hide_events** (*Optional*): Hide all events and renders just the headers, default `false`

- **show_only_disturbances** (*Optional*): Renders just disturbances in the traffic, default `false`