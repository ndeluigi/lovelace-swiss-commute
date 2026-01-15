[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# swiss-stationboard
Custom lovelace card for Home Assistant Lovelace UI.  
Swiss public transport stationboard. Shows connections from one or multiple stations.

![Stationboard "Schüpfen"](https://github.com/neuhausf/lovelace-swiss-stationboard/blob/main/img/stationboard-1.png?raw=true "Stationboard Schüpfen")

## Fork Information

This is a modified version of the original [lovelace-swiss-stationboard](https://github.com/neuhausf/lovelace-swiss-stationboard) by neuhausf.

**Added features:**
- **`via_filter`**: Filter departures by intermediate stops (not just final destination). For example, show only trains from Lausanne that stop at Sion, even if the final destination is Brig.

Original project: https://github.com/neuhausf/lovelace-swiss-stationboard

## Information

_**Warning:** Requires https://github.com/neuhausf/swiss-public-transport-mod to be installed first._  
Note that the current implementation is based on https://pypi.org/project/python-opendata-transport/ which currently doesn't return *delays* (property is there, but the underlying API-call to transport.opendata.ch may not always provide them).

## Configuration

- Go to HACS
- Add a custom repo: https://github.com/neuhausf/lovelace-swiss-stationboard
- Install the lovelace card

Add a new custom card to your Dashboard:

```YAML
type: custom:swiss-stationboard
name: Abfahrt
hide_title: true
platform_filter: 21
category: B|^ICE$|S
destination_filter: Bern|Zürich
max_rows: 6
name_replacement:
  Aeroporto: Airprt
  Malpensa: Malp
platform_name: Gl.
entity:
  - sensor.schupfen
```

### Card settings

* `name`: overrides the `friendly_name` inferred from the corresponding entity. Used as title.
* `departure_offset`: optional number of minutes (defaults to 0). Hides next departures within this window.
* `departure_countdown`: optional minutes (defaults to 15). Departures in this window show a countdown.
* `show_seconds`: show seconds in the countdown when true.
* `entity`: the sensor (from *swiss-public-transport-mod*) used as data source.
* `hide_title`: hides the card title when true.
* `vertical_title`: forces a small, vertical title on the left side of the card. The vertical title is also applied, if the card is smaller than 400px (horizontally).
* `name_replacement`: replace destination names (see examples below).
* `category`: optional regex to filter by category (e.g. `B|^ICE$|S`).
* `platform_filter`: optional regex to filter platforms (e.g. `3|21`).
* `show_last_changed`: shows when the underlying data last changed.
* `minutes_label`: string for minutes in ETA (defaults to ` min`/` mins`).
* `seconds_label`: string for seconds in ETA (defaults to `″`).
* `line_colors`: mapping to override the line background color per line. Keys are the displayed line text (e.g. `S3`, `IR68`) or regex-keys written as strings starting and ending with `/` (for example `/^S\\d+/`). Values are CSS colors (`#RRGGBB`, `rgb()`, color names). Only `background-color` is overridden; other styles remain.
* `destination_filter`: optional regex to filter by destination. Can be a single regex string (e.g. `Bern|Zürich`) or a list of regex strings (e.g. `["Bern", "Zürich", "^Basel"]`). If a list is provided, a connection matches when any entry matches.
* `via_filter`: optional string to filter departures by intermediate stops. Shows only journeys that pass through the specified station, even if it's not the final destination. For example, `via_filter: Sion` will show trains from Lausanne to Brig that stop at Sion. Supports regex matching by default (case-insensitive). Advanced options:
  * `via_filter_case_sensitive`: set to `true` for case-sensitive matching (default: `false`)
  * `via_filter_regex`: set to `false` to disable regex and use substring matching only (default: `true`)
  * `via_filter_fallback_include`: set to `true` to include journeys with missing stop data (default: `false`)
* `max_rows`: optional number (defaults to 0). Limits the number of rows shown (0 = unlimited).

Short example:
```yaml
type: 'custom:swiss-stationboard'
entity: sensor.sbb_stationboard_<id>
destination_filter:
  - Bern
  - Zürich
  - "^Basel"
max_rows: 8
line_colors:
  S3: "#1E90FF"
  IR68: "#FF8800"
  "/^S\\d+/": "#2d327d"
```

Example with intermediate stop filtering:
```yaml
type: 'custom:swiss-stationboard'
entity: sensor.lausanne_stationboard
via_filter: Sion
max_rows: 5
```
This configuration shows only departures from Lausanne that stop at Sion, even if the final destination is Brig, Visp, or another station beyond Sion.

### Text replacement 
#### Exact text replacement

Replaces occurrences in the destination name (e.g., `journey.to`). Matching is **literal**.

```yaml
type: custom:swiss-stationboard
name: Departures
hide_title: true
platform_filter: 21
category: B|^ICE$|S
platform_name: Pl.
name_replacement:
  Aeroporto: Airprt
  Malpensa: Malp
entity:
  - sensor.schupfen
```

#### Advanced format: list of replacement rules

Also supported as a list of rules (ordered):

```yaml
name_replacement:
  - from: Aeroporto
    to: Airprt
  - from: Malpensa
    to: Malp
```

#### Notes

* Replacements are applied globally (all occurrences).
* Matching is case-sensitive by default.

## Privacy 

This integration uses:

- https://github.com/agners/swiss-public-transport-card 
- the changes made in the pull request by @agners: https://github.com/home-assistant/core/pull/30715
- and some own code to adapt the visualization.
