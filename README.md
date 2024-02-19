# Pentair Intellicenter for Home Assistant

[![hacs][hacsbadge]][hacs]
[![GitHub Release][releases-shield]][releases]

## Installation

### From HACS

1. Install HACS if you haven't already (see [installation guide](https://hacs.netlify.com/docs/installation/manual)).
2. Add custom repository `https://github.com/dwradcliffe/intellicenter` as "Integration" in the settings tab of HACS.
3. Find and install "Pentair Intellicenter" integration in HACS's "Integrations" tab.
4. Restart your Home Assistant.
5. 'Pentair Intellicenter' should appear thru discovery in your Home Assistant Integration's page

### Features

- Connect to a Pentair Intellicenter thru the local (network) interface
- supports Zeroconf discovery
- reconnects itself gracefully in the Intellicenter reboots and/or gets disconnected
- "Local push" makes system very responsive
- The integration works independently of the security setting on the Intellicenter

### Entities created

- for each body of water (like Pool and Spa) it creates:
    - a switch to turn the body on and off
    - a sensor for the last temperature
    - a sensor for the desired temperature
    - a water heater entity (if applicable):
        - choose a heater from the list to enable it, set to OFF otherwise
        - status is 'OFF', 'IDLE' (if heater is enabled but NOT running) or
          'ON' is the heater is currently running
        Note that the water heater supports turn_on and turn_off operations.
        for turn_on, it will reuse the last heater chosen.
- for each heater, a binary sensor will indicate is the heater is running
  independently of which body is heating
- creates a switch for all circuits marked as "Featured" on the IntelliCenter
  (for example "Cleaner" or "Spa Blower)
- for each light (and light show) it creates a Light entity
  Note that color effects are only supported for IntelliBrite or MagicStream lights
- for each schedule, a binary_sensor will indicate if the schedule is currently running
  Note that these entities are disabled by default
- if the pool has a IntelliChem unit, sensors will be created for
  ph level, ORP level, ph tank level and ORP tank level
- a switch controls "Vacation mode". It's disabled by default
- for each pump, a binary_sensor is created
  if the pump supports these features, sensors will reflect power consumption, RPM and GPM
  Note that the power usage is rounded to the nearest 25W to reduced the amount of changes in HA
  Also note that depending on the setting of the pump, RPM or GPM can fluctuate constantly.
- a binary_sensor will indicate if the system is in Freeze prevention mode
- sensors will be created for each sensor in the system (like Water and Air)
  Note that a Solar sensor might also be present even if (like in my case) its value
  is not relevant

### Examples

<img src="device_info.png" width="400"/>

<img src="entities.png" width="400"/>

### Caveats

- while I tried to make the code as robust as possible I could only test using
  my own pool configuration. In particular, I do not have covers, chemistry, cascades,
  multiple heaters, etc... These may work out of the box or not...
- while the choice is metric/english on the Intellicenter is handled, changing it
  while the integration is running can lead to some values being off.
- In general it is recommended to reload the integration where significant changes are done to the pool configuration

[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange
[releases-shield]: https://img.shields.io/github/v/release/dwradcliffe/intellicenter
[releases]: https://github.com/dwradcliffe/intellicenter/releases
