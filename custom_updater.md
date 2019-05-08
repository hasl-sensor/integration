Custom Updater for HASL
===============================

This component is not part of the official distribution but can be updated with the help of Custom Updater.
For more information, see [[custom_updater](https://github.com/custom-components/custom_updater/wiki/Installation)]

## Automatic update of components
For update check of this sensor, add the following to your `configuration.yaml`.

```yaml
custom_updater:
  track:
    - components
  component_urls:
    - https://raw.githubusercontent.com/DSorlov/ha-sensor-sl/hasl/custom_updater.json
```

## Automatic update of cards
For update check of cards, add the following to your `configuration.yaml`.

```yaml
custom_updater:
  track:
    - cards
  card_urls:
    - https://raw.githubusercontent.com/DSorlov/ha-sensor-sl/hasl/custom_cards.json
```

## Automatic update of everything
For update check of this sensor and cards, add the following to your `configuration.yaml`.

```yaml
custom_updater:
  track:
    - components
    - cards
  component_urls:
    - https://raw.githubusercontent.com/DSorlov/ha-sensor-sl/hasl/custom_updater.json
  card_urls:
    - https://raw.githubusercontent.com/DSorlov/ha-sensor-sl/hasl/custom_cards.json
```



