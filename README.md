![maintained](https://img.shields.io/maintenance/yes/2022.svg)
[![hacs_badge](https://img.shields.io/badge/hacs-default-green.svg)](https://github.com/custom-components/hacs)
[![ha_version](https://img.shields.io/badge/home%20assistant-2021.12%2B-green.svg)](https://www.home-assistant.io)
![version](https://img.shields.io/badge/version-3.1.1-green.svg)
[![maintainer](https://img.shields.io/badge/maintainer-dsorlov-blue.svg)](https://github.com/DSorlov)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Swedish Public Transport Sensor (HASL)
======================================

## Project formerly known as "Home Assistant SL integration"

This is an Home Assistant integration providing sensors for Stockholms Lokaltrafik primaryly however it does support Resrobot and travels in the whole country. It provides intelligent sensors for departures, deviations, vehicle locations, traffic status and route monitoring using the SL official APIs and departures, arrivals and route monitoring using Resrobot. It also provides services for Location ID lookup and Trip Planing. You will still need to get your own API keys from SL / Trafiklab (se docs for [HASL](https://hasl.sorlov.com)). 

Full and detailed documentation is available [http://hasl.sorlov.com](http://hasl.sorlov.com).

## Install using HACS

* If you haven't already you must have [HACS installed](https://hacs.xyz/docs/setup/download).
* Go into HACS and search for HASL under the Integrations headline. You will need to restart Home Assistant to finish the process.
* Once that is done reload your GUI (caching issues preventing the integration to be shown).
* Goto Integrations and add HASL integrations.
* Get API-keys at TrafikLab, read details in [documentation](https://hasl.sorlov.com/trafiklab)
* [Location IDs](https://hasl.sorlov.com/locationid) can be found using services
* Perhaps add some GUI/Lovelace components as examples shows in the [documentation](https://hasl.sorlov.com/lovelace_cards)
* Enjoy and [buy me a coffee](https://www.buymeacoffee.com/sorlov) if you like my work

## Visualisation

The sensors should be able to be used multiple cards in hasl-cards ([departure-card](https://github.com/hasl-platform/lovelace-hasl-departure-card), [traffic-status-card](https://github.com/hasl-platform/lovelace-hasl-traffic-status-card)) . There are several cards for different sensors and presentation options for each sensor type. [More examples](https://hasl.sorlov.com/lovelace_cards) can be found in the [documentation](https://hasl.sorlov.com/).

![card](https://user-images.githubusercontent.com/8133650/56198334-0a150f00-603b-11e9-9e93-92be212d7f7b.PNG)


