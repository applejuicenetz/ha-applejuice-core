# appleJuice Core Integration für Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
![install_badge](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.applejuice_core.total)

appleJuice Core Integration für Home Assistant.

[![](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=applejuicenetz&repository=ha-applejuice-core&category=integration)

## manuelle Installation

1. Öffnen [HACS](https://hacs.xyz) in Home Assistant

2. Klicke auf die drei Punkte in der oberen rechten Ecke und wähle "Benutzerdefinierte Repositories"

3. Füge ein neues benutzerdefiniertes Repository hinzu:

    - **URL:** `https://github.com/applejuicenetz/ha-applejuice-core`

    - **Kategorie:** `Integration`

4. Klicke auf `Hinzufügen`

5. Klicke die `appleJuice Core` Integration

6. Klicke auf `HERUNTERLADEN`

7. starte `Home Assistant` neu

8. Navigiere zu `Einstellungen` - `Geräte & Dienste`

9. Klicke auf `INTEGRATION HINZUFÜGEN` und wähle die `appleJuice Core` Integration

10. Gib `Host/IP`, `XML-Port` und das appleJuice Core `Passwort` ein und klicke auf `OK`

## debugging

in der `configuration.yaml` kannst du das Logging-Level für die `appleJuice Core` Integration anpassen:

```yaml
logger:
  default: warning
  logs:
    custom_components.applejuice_core: debug
```

## Screenshot

![](./docs/integration_screenshot_settings.png)
![](./docs/integration_screenshot_core.png)
![](./docs/integration_screenshot_network.png)