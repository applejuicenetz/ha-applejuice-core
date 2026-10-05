"""Integration tests against a mocked appleJuice Core."""

import hashlib

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.applejuice_core.api import parse_version
from custom_components.applejuice_core.const import DOMAIN

HOST, PORT = "core.local", 9851
BASE = f"http://{HOST}:{PORT}"
PW_HASH = hashlib.md5(b"secret").hexdigest()

INFORMATION = (
    '<applejuice><generalinformation><version>{version}</version>'
    '<system>Linux</system></generalinformation></applejuice>'
)
MODIFIED = (
    '<applejuice><information credits="2147483648" sessionupload="1073741824" '
    'sessiondownload="0" uploadspeed="1048576" downloadspeed="0" openconnections="5"/>'
    '<networkinfo users="100" files="5" filesize="2,5" firewalled="false" paused="false" '
    'connectedwithserverid="7" connectedsince="1700000000000"/>'
    '<server id="7" host="srv.example"/>'
    '<download id="1" status="0"/><download id="2" status="18"/><upload id="3"/></applejuice>'
)
SHARE = '<applejuice><shares><share id="1" size="1073741824"/></shares></applejuice>'
SETTINGS = (
    '<settings><nick>leo</nick><autoconnect>true</autoconnect>'
    '<maxupload>102400</maxupload><maxdownload>0</maxdownload>'
    '<maxconnections>400</maxconnections><maxsourcesperfile>500</maxsourcesperfile>'
    '<speedperslot>50</speedperslot><maxnewconnectionsperturn>10</maxnewconnectionsperturn></settings>'
)


def mock_core(mocker: AiohttpClientMocker, version: str = "0.35.185.94") -> None:
    """Register the XML endpoints."""
    mocker.get(f"{BASE}/xml/information.xml", text=INFORMATION.format(version=version))
    mocker.get(f"{BASE}/xml/modified.xml", text=MODIFIED)
    mocker.get(f"{BASE}/xml/share.xml", text=SHARE)
    mocker.get(f"{BASE}/xml/settings.xml", text=SETTINGS)
    mocker.get(f"{BASE}/function/setsettings", text="ok")
    mocker.get(f"{BASE}/function/sharecheck", text="ok")
    mocker.get(f"{BASE}/function/exitcore", text="ok")


def make_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{HOST}:{PORT}",
        data={"url": HOST, "port": PORT, "password": "secret", "tls": False},
    )


async def setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def entity_id(hass: HomeAssistant, platform: str, key: str, entry) -> str | None:
    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{entry.entry_id}_{key}")


def test_parse_version() -> None:
    assert parse_version("0.35.185.94") > parse_version("0.35.185.93")
    assert not parse_version("0.35.185.93") > parse_version("0.35.185.93")
    assert parse_version("0.35.185.100") > parse_version("0.35.185.93")
    assert parse_version(None) is None
    assert parse_version("abc") is None


async def test_setup_and_states(hass: HomeAssistant, aioclient_mock) -> None:
    mock_core(aioclient_mock)
    entry = make_entry()
    await setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED

    assert hass.states.get(entity_id(hass, "sensor", "credits", entry)).state == "2.0"
    assert hass.states.get(entity_id(hass, "sensor", "downloads_total", entry)).state == "2"
    assert hass.states.get(entity_id(hass, "sensor", "downloads_paused", entry)).state == "1"
    assert hass.states.get(entity_id(hass, "sensor", "connected_server_name", entry)).state == "srv.example"
    assert hass.states.get(entity_id(hass, "sensor", "shared_size", entry)).state == "1.0"
    assert hass.states.get(entity_id(hass, "number", "setting_maxupload", entry)).state == "100"
    assert hass.states.get(entity_id(hass, "switch", "setting_autoconnect", entry)).state == "on"
    assert hass.states.get(entity_id(hass, "text", "setting_nickname", entry)).state == "leo"
    assert hass.states.get(entity_id(hass, "binary_sensor", "firewalled", entry)).state == "off"

    # Passwort-Hash wird als Query mitgeschickt, nie im Klartext.
    assert all(PW_HASH in str(call[1]) for call in aioclient_mock.mock_calls)
    assert all("secret" not in str(call[1]) for call in aioclient_mock.mock_calls)


async def test_writing_settings(hass: HomeAssistant, aioclient_mock) -> None:
    mock_core(aioclient_mock)
    entry = make_entry()
    await setup(hass, entry)

    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": entity_id(hass, "number", "setting_maxupload", entry), "value": 200}, blocking=True,
    )
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id(hass, "switch", "setting_autoconnect", entry)}, blocking=True,
    )
    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": entity_id(hass, "text", "setting_nickname", entry), "value": "neu name"}, blocking=True,
    )
    urls = [str(c[1]) for c in aioclient_mock.mock_calls if "setsettings" in str(c[1])]
    assert any("maxupload=204800" in u for u in urls)
    assert any("autoconnect=false" in u for u in urls)
    assert any("nickname=neu+name" in u for u in urls)


@pytest.mark.parametrize(("version", "expected"), [
    ("0.35.185.93", False),
    ("0.35.185.94", True),
    ("0.36.0.1", True),
    ("garbage", False),
])
async def test_sharecheck_button_version_gate(hass: HomeAssistant, aioclient_mock, version, expected) -> None:
    mock_core(aioclient_mock, version)
    entry = make_entry()
    await setup(hass, entry)
    assert (entity_id(hass, "button", "sharecheck", entry) is not None) is expected
    assert entity_id(hass, "button", "exitcore", entry) is not None


async def test_sharecheck_press(hass: HomeAssistant, aioclient_mock) -> None:
    mock_core(aioclient_mock)
    entry = make_entry()
    await setup(hass, entry)
    await hass.services.async_call(
        "button", "press", {"entity_id": entity_id(hass, "button", "sharecheck", entry)}, blocking=True
    )
    assert any("/function/sharecheck" in str(c[1]) for c in aioclient_mock.mock_calls)


async def test_wrong_password_triggers_reauth(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(
        f"{BASE}/xml/information.xml", status=302, headers={"Location": "/wrongpassword"}
    )
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert any(hass.config_entries.flow.async_progress_by_handler(DOMAIN))


async def test_unreachable_core_retries(hass: HomeAssistant, aioclient_mock) -> None:
    import aiohttp
    aioclient_mock.get(f"{BASE}/xml/information.xml", exc=aiohttp.ClientError)
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_config_flow_user(hass: HomeAssistant, aioclient_mock) -> None:
    mock_core(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"url": HOST, "port": PORT, "password": "secret", "tls": False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["port"] == PORT and isinstance(result["data"]["port"], int)

    # zweites Mal: doppelt
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"url": HOST, "port": PORT, "password": "secret", "tls": False}
    )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "already_configured"


async def test_config_flow_errors(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{BASE}/xml/information.xml", status=302, headers={"Location": "/wrongpassword"})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"url": HOST, "port": PORT, "password": "x", "tls": False}
    )
    assert result["errors"] == {"base": "invalid_auth"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"url": "http://bad", "port": PORT, "password": "x", "tls": False}
    )
    assert result["errors"] == {"url": "host_error"}


async def test_reauth_flow(hass: HomeAssistant, aioclient_mock) -> None:
    mock_core(aioclient_mock)
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"password": "new"})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reauth_successful"
    assert entry.data["password"] == "new"


async def test_options_flow_reloads(hass: HomeAssistant, aioclient_mock) -> None:
    mock_core(aioclient_mock)
    entry = make_entry()
    await setup(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"polling_rate": 60})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["polling_rate"] == 60
    assert entry.runtime_data.update_interval.total_seconds() == 60


async def test_unload(hass: HomeAssistant, aioclient_mock) -> None:
    mock_core(aioclient_mock)
    entry = make_entry()
    await setup(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
