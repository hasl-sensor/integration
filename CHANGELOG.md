# ha-sensor-sl

Changelog of this repo.

The format is based on [Keep a Changelog][keep-a-changelog]
<!-- and this project adheres to [Semantic Versioning][semantic-versioning]. -->

## Unreleased

### BREAKING CHANGES
- Changed structure in configuration to be more standarlized, avoid key duplication etc
- Cannot be used pre 0.92 as dependency code has moved (or atleast I have not tried it)
- New install location for the autoupdater (changed from folder sl to hasl)

### Changed
- Changed naming of a few functions to make it more clean
- Fixed issue #16: sync_interval not working
- Fixed issue #11: wrong time shown, thanks to [@isabellaalstrom] for suggesting fix
- Language is now picked from config first, then from browser, and then default sv-SE
- Icon changed to mdi:bus if no deviances, otherwise mdi:bus-alert
- Recomended install directory is now 'hasl' instead of 'sl' to align naming
- Fixed the autoupdater URLS (dev branch will be off but who cares, dev should not be used in prod)
- Using HASL 2.0.0 Communications Library with support for Trafikläget2 API from SL
- Implemented a request minimization strategy for API-calls / using caching (haslcache.json)

### Added
- Config 'property' in comb sensor to set which property that is reported as state
- Config 'always_show_time' in sl-card.js to force also showing time when less than 60 minutes to departure when 'timeleft' is set
- Added __init.py__ and manifest.json to support 0.92+ version of home assistant, thanks to [@dimmanramone] 
- Added property deviation_count to comb sensor to show number of deviations
- New sensor type TL2 for displaying trafic status messages
- Service for force clearing of cache (adds services.json)

## [v1.0.3] (2019-04-16)

### Changed
- Missing default value for direction parameter
- Integrated magic to better show time left to departure from fork [lokanx-home-assistant](https://github.com/lokanx-home-assistant/ha-sensor-sl/commit/df7de55f040a7fab5b15be176ec5d61400b1dbba)
- Added support for languages (sv-SE and en-EN) in sl-card.js

## [v1.0.2] (2019-04-16)

### Changed
- Fix for naming of unique_id for certain cases (still not good however)
- sl-card.js enhanced and styled by [@dimmanramone](https://github.com/dimmanramone)! Huge thanks!!

## [v1.0.1] (2019-04-15)

### Changed
- Fixed documtentation about interval being changed to scan_interval this to better support the Home Assistant standard.
- Fixed direction parameter that had been hardcoded for some strage reason. Blaming it on someone else. =)

## [v1.0.0] (2019-04-12)

### Added
- Added configuration for TimeWindow
- Added friendly_name (and removed name)
- Updated sl-card.js to support time or minutes departures
- Exposed unique_id for each sensor
- Added multiple properties to the sensor output

### Changed
- Moved communication to external PyPi library (HASL)
- Changed default repo from dev to hasl
- Cleaned up the code
- Using constant keywords from HomeAssistant
- If update error occures now deliver '-' as value instead of -1

### Removed
- name configuration (replaced by friendly_name)

## [v0.0.8] (2019-04-11)

### Changed
- Moved /sensor/sl.py to /sl/sensor.py
- Fixed bad formatting of custom_updater files
- Fixed custom_updater instructions in readme
- Fixed broken encoding issues for rendering in sl-card.js

## [v0.0.7] (2018-12-13)

### Added
- Rendering of deviances
- Parameters to customize card

### Changed
- Rendering strategy

## [v0.0.6] (2018-11-16)

### Added
- Added output of icons

### Changed
- Buggfixes in lookup
- Changed rendering in lovelace card

## [v0.0.5] (2018-11-16)

### Added
- Dependency for new https://www.trafiklab.se/api/sl-storningsinformation-2
- Lovelace card

### Changed
- Logging strings changed to indicate which api failed
- User Agent String conforms to standard
- Now renders the next hour of departures

### Removed
- JavaScript output

## [v0.0.4] (2018-09-30)

[Full Changelog][v0.0.0-v0.0.4]

### Added
- Use a binary_sensor to enable/disable API-calls
- Log error code and message once in case of error at API call
- Support for custom_updater

### Changed
- Log error message instead of just reporting failure.

[keep-a-changelog]: http://keepachangelog.com/en/1.0.0/
[v1.0.4]: https://github.com/dsorlov/ha-sensor-sl/tree/v1.0.4
[v1.0.3]: https://github.com/dsorlov/ha-sensor-sl/tree/v1.0.3
[v1.0.2]: https://github.com/dsorlov/ha-sensor-sl/tree/v1.0.2
[v1.0.1]: https://github.com/dsorlov/ha-sensor-sl/tree/v1.0.1
[v1.0.0]: https://github.com/dsorlov/ha-sensor-sl/tree/v1.0.0
[v0.0.8]: https://github.com/dsorlov/ha-sensor-sl/tree/v0.0.8
[v0.0.7]: https://github.com/dsorlov/ha-sensor-sl/tree/v0.0.7
[v0.0.6]: https://github.com/dsorlov/ha-sensor-sl/tree/v0.0.6
[v0.0.5]: https://github.com/dsorlov/ha-sensor-sl/tree/v0.0.5
[v0.0.4]: https://github.com/fredrikbaberg/ha-sensor-sl/tree/v0.0.4
