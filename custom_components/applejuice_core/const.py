from homeassistant.const import Platform

DOMAIN = "applejuice_core"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

CONF_URL = "url"
CONF_PORT = "port"
CONF_PASSWORD = "password"
CONF_TLS = "tls"
CONF_OPTION_POLLING_RATE = "polling_rate"

TIMEOUT = 10
