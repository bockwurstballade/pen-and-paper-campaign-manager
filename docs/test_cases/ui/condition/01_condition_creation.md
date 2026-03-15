# UI-Testfall: 01 - Zustand erstellen und speichern

## Ziel
Sicherstellen, dass ein neuer Zustand (Condition) über den Zustands-Manager korrekt angelegt und als eigenständiges JSON direkt unter `data/conditions/` gespeichert wird.

## Voraussetzungen
* Die Applikation wurde frisch gestartet (`python3 campaign-manager.py`).
* Der Ordner `data/conditions/` ist beschreibbar.

## Testdaten
* **Name:** "Panik"
* **Beschreibung:** "Der Charakter handelt irrational und flieht."
* **Art der Auswirkung:** "Malus"
* **Ziel der Auswirkung:** "Geistesblitzpunkte: Handeln"
* **Modifikator:** "-5"

## Vorbereitung
1. Navigiere vom Hauptmenü zu `Item / Zustands Manager`. Im Aufklapp-Menü ("Zustand bearbeiten" etc.) wähle "Neuen Zustand" bzw. klicke auf den entsprechenden Reiter.
   * Alternativ: Öffne die Charaktererstellung, Reiter "Zustände", klicke "+ Neuer Zustand" und setze den Haken bei "In globale Sammlung speichern".

## Ausführung
1. **Name eingeben:** Tippe `Panik` ein.
2. **Beschreibung:** Trage die o.g. Beschreibung ein.
3. **Auswirkungen:**
   * Wähle als Art der Auswirkung `Malus` (oder direkt das Ziel, falls die UI das kombiniert).
   * Wähle als Ziel `Geistesblitzpunkte: Handeln`.
   * Trage als Modifikator `-5` ein.
4. **Speichern:**
   * Klicke unten auf `Zustand speichern`.

## Erwartetes Ergebnis
* Der Info-Dialog "Erfolg" meldet, dass der Zustand gespeichert wurde.
* Im Ordner `data/conditions/` liegt eine neue Datei.
* Der Dateiname beginnt mit dem bereinigten Namen und endet auf die UUID, z. B. `Panik - 12345678-.....json`.
* Die JSON-Datei enthält alle oben eingetippten Schlüssel und Werte (z. B. `"effect_type": "Malus"`, `"effect_value": -5`).

## Cleanup
* Die neu erstellte Datei aus dem `data/conditions/`-Ordner löschen, falls nicht mehr gebraucht.
