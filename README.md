![maintained](https://img.shields.io/maintenance/yes/2026.svg)
![version](https://img.shields.io/badge/version-4.0.0-green.svg)
[![ha_version](https://img.shields.io/badge/home%20assistant-2026.2%2B-green.svg)](https://www.home-assistant.io)
[![hacs_badge](https://img.shields.io/badge/hacs-default-green.svg)](https://github.com/custom-components/hacs)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Swedish Public Transport Sensor (HASL)

> Project formerly known as "Home Assistant SL integration"

This is an Home Assistant integration providing sensors for [Stockholms Lokaltrafik (SL)](https://sl.se/) primarily, though it does support [Resrobot](https://resrobot.se/) and journeys in the whole country. This integration provides intelligent sensors for departures, traffic status and route monitoring using the SL official APIs and departures, arrivals and route monitoring using Resrobot. It also provides services for Location ID lookup and Trip Planing.

> To use Resrobot integration, you will need to get your own API key from Trafiklab (see docs for [HASL](https://hasl.sorlov.com)).

Full and detailed documentation [is available](http://hasl.sorlov.com).

## Install using HACS

* If you haven't already, you must have [HACS installed](https://hacs.xyz/docs/setup/download).
* Go into _HACS_ and search for _HASL_ under the _Integrations_ headline. Install the integration.
  * You will need to restart Home Assistant to finish the process.
* Once that is done reload your GUI (caching issues preventing the integration to be shown).
* Go to _Integrations_ and add _HASL integrations_.
  * For some of the integrations you might needd to obtain an API key from TrafikLab. Read details in [documentation](https://hasl.sorlov.com/trafiklab)

* Perhaps add some GUI/Lovelace components as examples shows in the [documentation](https://hasl.sorlov.com/lovelace_cards)
* Enjoy!

## Visualization

The sensors should be able to be used with [HASL Departure Card](https://github.com/hasl-sensor/lovelace-hasl-departure-card) of versions 3.2.0 and above.

![HASL Departure Card](https://github.com/hasl-sensor/lovelace-hasl-departure-card/raw/master/images/dark-card.png)

The "Disruptions" card is currently in development

### Legacy versions (< 3.2.0)

> Most of the APIs used by those versions are no longer available, so it is recommended to update to the latest version of the integration. If you want to use the older versions, you will need to use the older versions of the cards as well.

The sensors should be able to be used multiple cards in hasl-cards ([departure-card](https://github.com/hasl-platform/lovelace-hasl-departure-card), [traffic-status-card](https://github.com/hasl-platform/lovelace-hasl-traffic-status-card)) . There are several cards for different sensors and presentation options for each sensor type. [More examples](https://hasl.sorlov.com/lovelace_cards) can be found in the [documentation](https://hasl.sorlov.com/).

![card](https://user-images.githubusercontent.com/8133650/56198334-0a150f00-603b-11e9-9e93-92be212d7f7b.PNG)


## Support the developers

If you enjoy this integration, consider supporting the developers to help keep it running smoothly and enhance future updates.

- [@DSorlov](https://www.buymeacoffee.com/sorlov) - author of the original
- [@NecroKote](https://buymeacoffee.com/mkukhta) - maintainer
