"""Support for transport.opendata.ch."""
from __future__ import annotations

from datetime import timedelta
import logging
import asyncio

from opendata_transport import OpendataTransport, OpendataTransportStationboard
from opendata_transport.exceptions import OpendataTransportError
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity import Entity
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

ATTR_UNIQUE_ID = "unique_id"
ATTR_DEPARTURE_TIME1 = "next_departure"
ATTR_DEPARTURE_TIME2 = "next_on_departure"
ATTR_DURATION = "duration"
ATTR_PLATFORM = "platform"
ATTR_REMAINING_TIME = "remaining_time"
ATTR_START = "start"
ATTR_TARGET = "destination"
ATTR_TRAIN_NUMBER = "train_number"
ATTR_TRANSFERS = "transfers"
ATTR_DELAY = "delay"
ATTR_CONNECTIONS = "connections"
ATTR_DEPARTURES = "departures"

ATTRIBUTION = "Data provided by transport.opendata.ch"

CONF_DESTINATION = "to"
CONF_START = "from"
CONF_STATIONBOARD = "stationboard"
CONF_LIMIT = "limit"

DEFAULT_NAME = "Next Departure"

ICON = "mdi:bus"

SCAN_INTERVAL = timedelta(seconds=90)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_DESTINATION): cv.string,
        vol.Optional(CONF_START): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_STATIONBOARD): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_LIMIT): cv.positive_int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

async def test_opendata(opendata):
    """Test wheather the current configuration allows to get data."""

    try:
        data = await opendata.async_get_data()
        _LOGGER.debug(data)
    except OpendataTransportError:
        _LOGGER.error(
            "Check at http://transport.opendata.ch/examples/stationboard.html "
            "if your station names are valid"
        )
        return False
    return True

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Swiss public transport sensor."""

    unique_id = config.get(ATTR_UNIQUE_ID)
    name = config.get(CONF_NAME)
    start = config.get(CONF_START)
    destination = config.get(CONF_DESTINATION)
    stationboard = config.get(CONF_STATIONBOARD)
    limit = config.get(CONF_LIMIT, 5)

    session = async_get_clientsession(hass)

    entities = []

    if start is not None and destination is not None:
        opendata = OpendataTransport(start, destination, session, limit)
        if await test_opendata(opendata):
            entities.append(SwissPublicTransportSensor(opendata, name))

    if stationboard is not None:
        opendata = OpendataTransportStationboard(
            stationboard, session, limit
        )
        if await test_opendata(opendata):
            entities.append(SwissPublicTransportStationboardSensor(opendata, session, name, unique_id, stationboard))

    async_add_entities(entities)


class SwissPublicTransportStationboardSensor(SensorEntity):
    """Implementation of an Swiss public transport stationboard sensor."""

    def __init__(self, opendata, session, name, unique_id, stationboard=None):
        """Initialize the sensor."""
        self._opendata = opendata
        self._session = session
        self._name = name
        self._remaining_time = ""
        self._attr_unique_id = unique_id
        # Store the stationboard list for later use
        self._stationboard = stationboard if stationboard else []

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return (
            self._opendata.journeys[0]["departure"]
            if self._opendata is not None and len(self._opendata.journeys) > 0
            else None
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self._opendata is None or len(self._opendata.journeys) < 1:
            return

        self._remaining_time = dt_util.parse_datetime(
            self._opendata.journeys[0]["departure"]
        ) - dt_util.as_local(dt_util.utcnow())

        return {
            ATTR_DEPARTURES: self._opendata.journeys,
            ATTR_TRAIN_NUMBER: self._opendata.journeys[0]["number"],
            ATTR_PLATFORM: self._opendata.journeys[0]["platform"],
            ATTR_REMAINING_TIME: f"{self._remaining_time}",
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    async def async_update(self):
        """Get the latest data from opendata.ch and update the states."""
        _LOGGER.info("async_update called")
        try:
            self._opendata.journeys = []
            await self._opendata.async_get_data()
            
            # Enhance journey data with intermediate stops
            await self._enhance_with_stops()

        except OpendataTransportError:
            _LOGGER.error("Unable to retrieve data from transport.opendata.ch")
    
    async def _enhance_with_stops(self):
        """Fetch detailed stationboard data with passList for all journeys."""
        import aiohttp
        from urllib.parse import quote
        
        # Get station name from stored stationboard list
        station_name = self._stationboard[0] if self._stationboard and len(self._stationboard) > 0 else None
        if not station_name:
            _LOGGER.warning("No station name available for enhancing stop data")
            return
        
        # Build API URL with higher limit to get detailed data
        # Don't use fields parameter as it filters out other necessary data
        limit = len(self._opendata.journeys) + 5  # Get a few extra to ensure we have all
        url = f"https://transport.opendata.ch/v1/stationboard?station={quote(station_name)}&limit={limit}"
        
        try:
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    _LOGGER.warning(f"Failed to fetch enhanced stationboard data: HTTP {response.status}")
                    return
                
                data = await response.json()
                
                if 'stationboard' not in data:
                    return
                
                # Create a lookup map for enhanced data
                enhanced_map = {}
                for item in data['stationboard']:
                    # Create a unique key for matching
                    departure_time = item.get('stop', {}).get('departure')
                    destination = item.get('to')
                    category = item.get('category')
                    number = item.get('number', '')
                    
                    if departure_time and destination:
                        key = f"{departure_time}_{destination}_{category}_{number}"
                        enhanced_map[key] = item
                
                # Enhance each journey with stop data
                for journey in self._opendata.journeys:
                    # Create matching key
                    key = f"{journey.get('departure')}_{journey.get('to')}_{journey.get('category')}_{journey.get('number', '')}"
                    
                    if key in enhanced_map:
                        enhanced_item = enhanced_map[key]
                        
                        # Extract passList if available
                        if 'passList' in enhanced_item:
                            journey['passList'] = enhanced_item['passList']
                            
                            # Extract stop names from passList
                            stops = []
                            for stop in enhanced_item['passList']:
                                if 'station' in stop and 'name' in stop['station']:
                                    stops.append(stop['station']['name'])
                            journey['stops'] = stops
                        else:
                            journey['stops'] = []
                            journey['passList'] = []
                    else:
                        journey['stops'] = []
                        journey['passList'] = []
                        
        except Exception as e:
            _LOGGER.error(f"Failed to enhance journeys with stop data: {e}", exc_info=True)

class SwissPublicTransportSensor(Entity):
    """Implementation of an Swiss public transport sensor."""

    def __init__(self, opendata, name):
        """Initialize the sensor."""
        self._opendata = opendata
        self._name = name
        self._remaining_time = ""

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return (
            self._opendata.connections[0]["departure"]
            if self._opendata is not None
            else None
        )

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if self._opendata is None:
            return

        self._remaining_time = dt_util.parse_datetime(
            self._opendata.connections[0]["departure"]
        ) - dt_util.as_local(dt_util.utcnow())

        # Convert to a list since this is more approprate
        connections = [c[1] for c in sorted(self._opendata.connections.items())]

        attr = {
            ATTR_TRAIN_NUMBER: self._opendata.connections[0]["number"],
            ATTR_PLATFORM: self._opendata.connections[0]["platform"],
            ATTR_TRANSFERS: self._opendata.connections[0]["transfers"],
            ATTR_DURATION: self._opendata.connections[0]["duration"],
            ATTR_DEPARTURE_TIME1: self._opendata.connections[1]["departure"],
            ATTR_DEPARTURE_TIME2: self._opendata.connections[2]["departure"],
            ATTR_START: self._opendata.from_name,
            ATTR_TARGET: self._opendata.to_name,
            ATTR_REMAINING_TIME: f"{self._remaining_time}",
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_DELAY: self._opendata.connections[0]["delay"],
            ATTR_CONNECTIONS: connections,
        }
        return attr

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    async def async_update(self):
        """Get the latest data from opendata.ch and update the states."""

        try:
            await self._opendata.async_get_data()
        except OpendataTransportError:
            _LOGGER.error("Unable to retrieve data from transport.opendata.ch")
