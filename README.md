[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# Swiss Public Transport - Complete Solution

A comprehensive Home Assistant integration combining backend sensor and frontend card for Swiss public transport.

## Fork Information

This is an enhanced version combining:
- **Backend**: Modified [swiss-public-transport-mod](https://github.com/neuhausf/swiss-public-transport-mod) by neuhausf
- **Frontend**: Modified [lovelace-swiss-stationboard](https://github.com/neuhausf/lovelace-swiss-stationboard) by neuhausf

**Key enhancements:**
- ✨ **Intermediate stops data**: Sensor now fetches and exposes stop lists (passList) for each journey
- 🎯 **`via_filter`**: Filter departures by intermediate stops (e.g., show only trains from Lausanne that stop at Sion)
- 🚆 **Complete integration**: Both sensor and card in one repository

Original projects:
- https://github.com/neuhausf/swiss-public-transport-mod
- https://github.com/neuhausf/lovelace-swiss-stationboard

## Information

**Note:** You can use the data of this sensor on its own or use the custom lovelace-card to visualize a stationboard.

## Installation

### Step 1: Install the Integration (Backend Sensor)

- Go to HACS → Integrations
- Click the three dots menu (⋮) → Custom repositories
- Add this repository: `https://github.com/ndeluigi/swiss-transport-integration`
- Select category: "Integration"
- Click "Add"
- Find "Swiss Public Transport Mod" and click "Download"
- Restart Home Assistant

### Step 2: Install the Lovelace Card (Frontend)

The card is included in this repository under `lovelace-card/`.

- Go to HACS → Frontend
- Click the three dots menu (⋮) → Custom repositories
- Add this repository: `https://github.com/ndeluigi/swiss-transport-integration`
- Select category: "Lovelace"
- Click "Add"
- Find "Swiss Stationboard" and click "Download"
- Restart Home Assistant

### Step 3: Configure the Sensor

Add a new sensor to your `configuration.yaml`:

```YAML
sensor:
  - platform: swiss_public_transport_mod
    name: Schüpfen
    limit: 4
    stationboard:
    - Schüpfen
```

Note that you can aggregate multiple starting stations into the same sensor. For example, if multiple, surrounding bus/tram stations are to be included. For each station a `limit` maximum number of connections is fetched:

```YAML
sensor:
  - platform: swiss_public_transport_mod
    name: Bern
    limit: 4
    stationboard:
    - Bern
    - Bern, Hirschengraben
```

In this example, `limit` equals 4, so 4 connections are fetched starting from Bern and 4 connections starting from Bern, Hirschengraben (total 8):

<img src="https://user-images.githubusercontent.com/7963239/218667500-dddbdf45-9b1a-40a6-9c04-83a018d25e26.png" width="300" >
(note that you need the [lovelace-card](https://github.com/neuhausf/lovelace-swiss-stationboard "lovelace-card") to visualize the sensor)


Multiple sensors with completely different output locations are also possible. To do this, simply duplicate the configuration:

```YAML
sensor:
  - platform: swiss_public_transport_mod
    name: Schüpfen
    limit: 4
    stationboard:
    - Schüpfen
  - platform: swiss_public_transport_mod
    name: Langenthal
    limit: 4
    stationboard:
    - Langenthal
```
... this will lead to:

<img src="https://user-images.githubusercontent.com/7963239/218668664-5f6b70ad-6e0a-410b-83a3-c90f174da738.png" width="300" >

## Lovelace Card Configuration

### Basic Card Setup

Add a new custom card to your Dashboard:

```yaml
type: custom:swiss-stationboard
entity: sensor.lausanne_stationboard
max_rows: 10
```

### Using the via_filter Feature

The `via_filter` allows you to show only trains that stop at a specific intermediate station:

```yaml
type: custom:swiss-stationboard
entity: sensor.lausanne_stationboard
name: Lausanne → Sion
via_filter: Sion
max_rows: 10
category: ^IR$|^EC$
```

This shows only IR and EC trains from Lausanne that stop at Sion, even if their final destination is Brig, Visp, or beyond.

### Advanced Card Options

```yaml
type: custom:swiss-stationboard
entity: sensor.lausanne_stationboard
name: Lausanne Departures
via_filter: Sion
via_filter_case_sensitive: false
via_filter_regex: true
via_filter_fallback_include: true
category: ^IR$|^EC$
destination_filter: /Aéroport|Fribourg/
departure_countdown: 60
max_rows: 10
line_colors:
  IC1: "#FF0000"
  IR90: "#0066CC"
platform_name: Voie
```

### Card Configuration Options

- **`entity`**: Your Swiss transport sensor (required)
- **`name`**: Override the card title
- **`via_filter`**: Filter by intermediate stop (e.g., `Sion`)
  - `via_filter_case_sensitive`: Case-sensitive matching (default: `false`)
  - `via_filter_regex`: Enable regex matching (default: `true`)
  - `via_filter_fallback_include`: Include trains with missing stop data (default: `false`)
- **`category`**: Filter by train type using regex (e.g., `^IR$|^EC$`)
- **`destination_filter`**: Exclude destinations using regex (wrap in `/pattern/` for regex mode)
- **`platform_filter`**: Filter by platform (e.g., `3|4|5`)
- **`departure_countdown`**: Show countdown for departures within X minutes (default: 15)
- **`departure_offset`**: Hide departures within X minutes (default: 0)
- **`max_rows`**: Limit displayed departures
- **`line_colors`**: Custom colors for specific lines
- **`name_replacement`**: Replace destination names
- **`platform_name`**: Custom platform label (e.g., `Gl.`, `Voie`)

### Example: Lausanne to Sion (IR/EC only)

```yaml
type: custom:swiss-stationboard
entity: sensor.lausanne_stationboard
name: Lausanne → Sion
category: ^IR$|^EC$
destination_filter: /Aéroport|Fribourg|Bern/
departure_countdown: 60
max_rows: 10
```

This configuration:
- Shows only IR and EC trains
- Excludes trains to Geneva Airport, Fribourg, and Bern (westbound)
- Shows trains going eastbound (Brig, Visp, etc.) which pass through Sion
- Displays countdown for trains departing within 60 minutes

## What's New in This Version

### Backend Enhancements
- **Intermediate stops data**: The sensor now fetches `passList` from the transport.opendata.ch API
- **Stop names exposed**: Each journey includes a `stops` array with all intermediate station names
- **Efficient fetching**: Single API call to get stop data for all journeys

### Frontend Enhancements
- **`via_filter`**: Filter departures by intermediate stops
- **Debug modes**: `via_filter_debug` and `category_debug` for troubleshooting
- **Flexible matching**: Regex and substring matching with case-sensitivity options

## Troubleshooting

### via_filter not working?

1. **Enable debug mode**:
   ```yaml
   via_filter_debug: true
   ```
   Check browser console (F12) for `[via_filter]` logs

2. **Check if sensor provides stop data**:
   - Go to Developer Tools → States
   - Find your sensor entity
   - Check if `departures` includes `stops` or `passList` fields

3. **Use fallback mode**:
   ```yaml
   via_filter_fallback_include: true
   ```

### Category filter not matching?

Enable debug to see actual category values:
```yaml
category_debug: true
```

## Privacy 

This integration uses:
- The changes made in the pull request by @agners: https://github.com/home-assistant/core/pull/30715
- Additional code to work with newer Home Assistant versions
- Direct API calls to transport.opendata.ch for enhanced data
