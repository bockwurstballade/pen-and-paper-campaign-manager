# UI-Testfall: 01 - Item erstellen und speichern

## Ziel
Sicherstellen, dass ein neues Item über den Item-Manager im Hauptmenü (oder aus der Charaktererstellung heraus) korrekt angelegt und fehlerfrei als eigenständiges JSON direkt unter `data/items/` abgespeichert wird.

## Voraussetzungen
* Die Applikation wurde frisch gestartet (`python3 campaign-manager.py`).
* Der Ordner `data/items/` ist beschreibbar.

## Testdaten
* **Name:** "Testschwert der Verdammnis"
* **Beschreibung:** "Ein glühendes Schwert für Testzwecke."
* **Ist Waffe:** Ja (Häkchen gesetzt)
* **Schadensformel:** "1d8+2"
* **Kategorie:** "Nahkampf" (oder ähnlich)
* **Attribut 1:** "Gewicht" -> "5 kg"
* **Zustand anfügen:** Optional, z.B. "Blutend"

## Vorbereitung
1. Navigiere vom Hauptmenü zu `Item / Zustands Manager`.
   * Alternativ: Öffne die Charaktererstellung, gehe zum Reiter "Items", klicke "+ Neues Item" und setze den Haken bei "In globale Sammlung speichern".

## Ausführung
1. **Name eingeben:** Tippe `Testschwert der Verdammnis` in das Namensfeld ein.
2. **Beschreibung:** Trage die o.g. Beschreibung ein.
3. **Waffen-Eigenschaften:** 
   * Setze den Haken bei `Waffe`.
   * Trage bei Schaden `1d8+2` ein.
   * Wähle als Kategorie `Nahkampf`.
4. **Attribute anlegen:**
   * Klicke auf `+ Eigenschaft`.
   * Name: `Gewicht`, Wert: `5 kg`.
5. **Speichern:**
   * Klicke unten auf `Item speichern`.

## Erwartetes Ergebnis
* Der Info-Dialog "Erfolg" erscheint und meldet, dass das Item gespeichert wurde.
* Im Ordner `data/items/` liegt eine neue Datei.
* Der Dateiname beginnt mit dem bereinigten Namen und endet auf die UUID, z. B. `Testschwert der Verdammnis - 12345678-.....json`.
* Die JSON-Datei enthält alle oben eingetippten Schlüssel und Werte (z. B. `"is_weapon": true`, `"damage_formula": "1d8+2"`).

## Cleanup
* Die neu erstellte Datei aus dem `data/items/`-Ordner löschen, falls nicht mehr gebraucht.
