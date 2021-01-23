DOMAIN = "mcp23017listner"

from adafruit_mcp230xx.mcp23017 import MCP23017
from homeassistant.helpers.entity import Entity
from .Stater import Stater
import board  # pylint: disable=import-error
import busio  # pylint: disable=import-error
import digitalio  # pylint: disable=import-error
import logging
import threading
import time
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

EVENT_NOTIFY = "mcp23017"
CONF_INVERT_LOGIC = "invert_logic"
CONF_I2C_ADDRESS = "i2c_address"
CONF_PINS = "pins"
CONF_PULL_MODE = "pull_mode"

MODE_UP = "UP"
MODE_DOWN = "DOWN"

DEFAULT_INVERT_LOGIC = False
DEFAULT_I2C_ADDRESS = 0x20
DEFAULT_PULL_MODE = MODE_UP

_LOGGER = logging.getLogger(__name__)

_SWITCHES_SCHEMA = vol.Schema({cv.positive_int: cv.string})
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_PINS): _SWITCHES_SCHEMA,
                vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
                vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): vol.All(
                    vol.Upper, vol.In([MODE_UP, MODE_DOWN])
                ),
                vol.Optional(CONF_I2C_ADDRESS, default=DEFAULT_I2C_ADDRESS): vol.Coerce(int),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def _monitor_events(hass, states):
    while True:
        for state in states:
            state.update_stater()
            time.sleep(0.01)


def _start_event_monitor(hass, states):
    thread = threading.Thread(
        target=_monitor_events,
        name=f"MCP230117",
        args=(hass, states),
        daemon=True,
    )
    thread.start()


# async def async_setup_entry(hass, config_entry, async_add_entities):

def setup(hass, config):
    """Set up the MCP23017 binary sensors."""
    pull_mode = config[DOMAIN][CONF_PULL_MODE]
    invert_logic = config[DOMAIN][CONF_INVERT_LOGIC]
    i2c_address = config[DOMAIN][CONF_I2C_ADDRESS]

    i2c = busio.I2C(board.SCL, board.SDA)
    mcp = MCP23017(i2c, address=i2c_address)

    states = []
    pins = config[DOMAIN][CONF_PINS]

    for pin_num, pin_name in pins.items():
        pin = mcp.get_pin(pin_num)
        states.append(
            MCP23017BinarySensor(pin_name, pin, pull_mode, invert_logic, hass)
        )

    _start_event_monitor(hass, states)

    # add_devices(states, True)

    return True


class MCP23017BinarySensor(Entity):
    """Represent a binary sensor that uses MCP23017."""

    def __init__(self, name, pin, pull_mode, invert_logic, hass):
        """Initialize the MCP23017 binary sensor."""
        self._name = name
        self._pin = pin
        self._pull_mode = pull_mode
        self._invert_logic = invert_logic
        self._state = None
        self._pin.direction = digitalio.Direction.INPUT
        self._pin.pull = digitalio.Pull.UP
        self._hass = hass
        self._stater = Stater(pin, self.fire)

    def fire(self, obj):
        _LOGGER.error(self._name + " " + obj["action"])
        self._hass.bus.fire(self._name, obj)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the entity."""
        return self._state != self._invert_logic

    def update_stater(self):
        self._stater.update(self._pin.value)

    def update(self):
        """Update the GPIO state."""
        self._state = self._pin.value