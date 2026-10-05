# ha-applejuice-core

Home-Assistant-Integration für den appleJuice Core (`custom_components/applejuice_core`). Nutzer-Doku steht in `README.md`, alles andere hier.

## Aufbau

- `api.py`: `AppleJuiceClient` (XML und `/function/*`), eigene Fehlertypen, `parse_version`. Redirects werden nicht verfolgt: der Core antwortet auf ein falsches Passwort mit 302 auf `/wrongpassword`, auf unbekannte Funktionen mit 302 auf `/help`.
- `coordinator.py`: lädt `modified.xml`, `share.xml`, `settings.xml` parallel und hängt sie unter einen Root. `settings.xml` liegt als Kindknoten `settings` darunter. Version und System kommen einmalig aus `information.xml` (`_async_setup`).
- `entity.py`: `AppleJuiceCoreEntity`, `AppleJuiceNetworkEntity`, `AppleJuiceSettingEntity` (Schreiben per `/function/setsettings`).
- Plattformen: `sensor`, `binary_sensor`, `button`, `number`, `switch`, `text`. Daten liegen in `entry.runtime_data`, kein `hass.data`.
- Core- und Network-Device werden in `__init__.py` registriert. Network hängt über `via_device_id` am Core; `via_device` in `DeviceInfo` ist deprecated.
- Share-Check-Button: nur sichtbar, wenn die Core-Version strikt größer als `SHARECHECK_AFTER_CORE_VERSION` (`const.py`) ist. Die Konstante auf die letzte öffentliche Core-Version setzen, sobald ein neuer Release erscheint. Der Core braucht dafür `/function/sharecheck`.
- Settings-Entities: Raten stehen im Core in Byte/s, die Entities zeigen KB/s (`divisor=1024`). Port, XML-Port und Verzeichnisse sind bewusst nicht änderbar. Der Core klemmt Werte selbst (z. B. `maxupload` min 3072 Byte/s, `maxconnections` min 30, `speedperslot` abhängig vom Upload).
- Nach dem Schreiben `coordinator.async_refresh()` verwenden, nicht `async_request_refresh()`: dessen Debounce liefert direkt nach dem Schreiben noch den alten Wert.
- Buttons zeigen bis zum ersten Druck `unknown`. `ButtonEntity.state` ist in Home Assistant `final`, daran lässt sich im Plugin nichts ändern.

## Tests

Unit- und Integrationstests laufen gegen echtes Home Assistant mit gemocktem Core:

```bash
python3 -m venv $TMPDIR/hav
$TMPDIR/hav/bin/pip install homeassistant pytest-homeassistant-custom-component
$TMPDIR/hav/bin/python -m pytest -q -p no:sugar
```

Auf dieser Maschine scheitert der Build von `lru-dict` (gepinnt). Dann `homeassistant` und `pytest-homeassistant-custom-component` mit `--no-deps` installieren, die Abhängigkeiten aus `importlib.metadata.requires(...)` ohne `lru-dict` per `pip install -r` nachziehen und `lru-dict` ungepinnt installieren. `defusedxml` zusätzlich installieren.

## Test mit echtem Home Assistant und Core (`test-env/`)

`test-env/compose.yaml` startet im Docker-Netz `applejuice-isolated_isolated` (aus `isolated-network/`, muss laufen) einen eigenen Core und Home Assistant. `isolated-network/runtime/core.jar` muss existieren.

| Dienst | Adresse | Zugang |
| --- | --- | --- |
| `core-ha` | `198.51.100.30:9851` | Passwort `ha` (MD5 `925cc8d2953eba624b2bfedf91a91613`) |
| `homeassistant` (Image `:stable`) | `http://127.0.0.1:8123`, im Netz `198.51.100.31` | Login `admin` / `admin` |
| `homeassistant-beta` (Image `:beta`, Profil `beta`) | `http://127.0.0.1:8124`, im Netz `198.51.100.32` | Login `admin` / `admin` |

Ablauf:

1. Bilder ziehen: `docker pull ghcr.io/home-assistant/home-assistant:stable` und `:beta`. Die Compose-Datei setzt `pull_policy: never`. Der Platz auf `/` ist knapp (Image ca. 3,4 GB je Tag): vorher `df -h /` prüfen.
2. Starten mit `docker compose up -d core-ha homeassistant` und `docker compose --profile beta up -d homeassistant-beta`, jeweils in `test-env/`. Das Terminal-Tool hält `up -d` für einen Dauerprozess; mit `background=true` und `notify=true` starten.
3. `python3 test-env/ha_provision.py <PORT>` (8123 oder 8124) legt beim ersten Lauf Benutzer und Onboarding an, richtet die Integration per Config-Flow ein (prüft auch das falsche Passwort) und testet das Schreiben aller Settings-Entities und den Clean-Download-List-Button. Das Skript läuft idempotent weiter, wenn die Instanz schon eingerichtet ist. Exit-Code 1 bei fehlgeschlagenen Schreibtests.
4. Home Assistant liest `custom_components/applejuice_core` direkt als Read-only-Bind-Mount. Nach Code-Änderungen `docker restart applejuice-ha-test-homeassistant-1` (bzw. `-beta-1`) und danach `docker logs` auf `applejuice` und Deprecation-Meldungen prüfen.
5. Der Core in `isolated-network/` läuft mit `0.35.185.1`. Der Share-Check-Button muss dort fehlen (Version nicht größer als die Grenze). Der Button lässt sich erst mit einem Core größer als `SHARECHECK_AFTER_CORE_VERSION` live testen.

Getestete Stände: Home Assistant `2026.9.4` (Python 3.14.6) und `2026.10.0b1`. Beide ohne Warnungen des Plugins im Log.
