# UI-Testfall: 01 - Kampagne erstellen und speichern

## Ziel
Sicherstellen, dass eine neue Kampagne über die "Neue Kampagne erstellen"-Schaltfläche im Hauptmenü korrekt mit allen Eingabewerten angelegt und fehlerfrei als JSON abgespeichert wird.

## Voraussetzungen
* Die Applikation wurde gestartet (`python3 campaign-manager.py`).
* Das Hauptfenster (Welcome Window) ist sichtbar.
* Der Ordner `data/campaigns/` ist beschreibbar.

## Testdaten
* **Titel:** Schatten über Waterdeep
* **Regelwerk:** D&D 5e
* **Art:** Kampagne (aus dem Dropdown)

## Ablauf

1. **Start:** Klicke im Hauptmenü auf die Schaltfläche **Neue Kampagne erstellen**.
2. **Daten eingeben:**
   * Trage in das Feld "Titel" den Wert `Schatten über Waterdeep` ein.
   * Trage in das Feld "Regelwerk" den Wert `D&D 5e` ein.
   * Wähle im Dropdown-Menü "Art" den Eintrag `Kampagne`.
3. **Speichern:**
   * Klicke auf den Button **💾 Kampagne speichern**.
4. **Bestätigung:**
   * Ein Info-Dialog "Erfolg" mit der Meldung "Kampagne erfolgreich gespeichert!" wird angezeigt.
   * Klicke auf "OK".
   * Der Dialog "Kampagne erstellen / bearbeiten" schließt sich automatisch.

## Erwartetes Ergebnis
* Der Dialog verhält sich fehlerfrei (kein Absturz).
* Im Verzeichnis `data/campaigns/` liegt eine neue Datei mit einem Namen wie `Schatten über Waterdeep - [UUID].json`.
* Beim Öffnen der JSON-Datei sind folgende Werte korrekt gespeichert:
  * `"title": "Schatten über Waterdeep"`
  * `"ruleset": "D&D 5e"`
  * `"type": "Kampagne"`
  * `"id": "[Eine gültige UUID]"`

## Cleanup
* Die neu erstellte Testdatei in `data/campaigns/` kann zum Aufräumen gelöscht werden.
