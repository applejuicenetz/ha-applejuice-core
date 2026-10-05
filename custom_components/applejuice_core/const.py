"""Constants for the appleJuice Core integration."""

from homeassistant.const import Platform

DOMAIN = "applejuice_core"

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
]

CONF_URL = "url"
CONF_PORT = "port"
CONF_PASSWORD = "password"
CONF_TLS = "tls"
CONF_OPTION_POLLING_RATE = "polling_rate"

DEFAULT_PORT = 9851
DEFAULT_POLLING_RATE = 30
MIN_POLLING_RATE = 5
MAX_POLLING_RATE = 3600

TIMEOUT = 10

# Button nur für Cores NEUER als diese Version (letzte öffentliche Version, exklusiv).
SHARECHECK_AFTER_CORE_VERSION = "0.35.185.93"
