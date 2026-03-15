# UI-Testfall: 01 - Charakter erstellen und speichern

## Ziel
Sicherstellen, dass ein neuer Spielercharakter (oder NSC) inkl. Base Stats, Attributen, Rüstung, Fähigkeiten, Items und Zuständen korrekt über die UI angelegt und als JSON im Dateisystem gespeichert werden kann.

## Voraussetzungen
* Die Applikation wurde frisch gestartet (`python3 campaign-manager.py`).
* Der Ordner `data/characters/` (und ggf. `data/campaigns/`) ist beschreibbar.

## Testdaten
* **Rolle:** Spielercharakter
* **Name:** Test-Held "Arthas"
* **Klasse:** Gärtner
* **Geschlecht:** Männlich
* **Alter:** 35
* **Lebenspunkte:** 40
* **Statur:** Groß
* **Grundschaden:** 1W6+2
* **Rüstung:** Plattenpanzer (Wert 5)
* **Fähigkeiten:** Handeln (Kategorie-Wert: 10), "Schlösser knacken" (Wert: 5)
* **Items:** 1x Fackel
* **Zustände:** 1x "Gute Laune" (+2 auf Soziales)

## Ablauf

1. **Start:** Klicke im Hauptfenster auf **Neuen Charakter erstellen**.
2. **Base Stats ausfüllen:**
   * Wähle als "Typ" `Spielercharakter`.
   * Gib unter "Name" den Wert `Test-Held "Arthas"` ein.
   * Trage bei "Klasse" `Krieger` ein.
   * Wähle als Geschlecht `Männlich`.
   * Setze "Alter" auf `35` und "Lebenspunkte" auf `40`.
   * Trage als Status `athletisch` ein.
   * Trage bei Religion `katholisch` ein.
   * Trage bei Beruf `Gärtner` ein.
   * Wähle Familienstand `ledig`.
   * Trage bei "Grundschaden" `1W6+2` ein.
   * Gib bei Schreibung folgendes ein:

   ```
   Arthas ist ein sehr motivierter Paladin der silbernen Hand.
   ```
3. **Rüstung definieren:**
   * Setze einen Haken bei "Rüstungsmodul aktivieren".
   * Trage bei "Rüstungswert" `4` und bei "Rüstungszustand" `9` ein.
4. **Fähigkeiten eintragen:**
   * Scrolle zum Bereich "Fähigkeiten & Attribute".
   * Klicke in der Sektion `Handeln` auf `+ Neue Fähigkeit`.
   * Wähle als Fähigkeitsname `Schwimmen` und klicke auf `OK`.
   * Vergib für Schwimmen den Wert `40`.
   * Füge im Bereich `Handeln` desweiteren noch hinzu
      ** `Schlösser knacken` mit Wert 30
      ** `Kochen` mit Wert 20
      ** `Klettern` mit Wert 10
   * Füge nun folgende Talenete im Bereich `Wissen` hinzu
     ** `Geschichte` mit Wert 40
     ** `Spanisch` mit Wert 60
     ** `Dämonologie` mit Wert 50
   * Füge nun folgende Talenete im Bereich `Soziales` hinzu
     ** `Einschüchtern` mit Wert 40
     ** `Verhandeln` mit Wert 60
     ** `Lügen` mit Wert 50
5. **Items hinzufügen:**
   * Gehe zum Reiter/Bereich "Items".
   * Klicke auf `+ Neues Item`.
   * Wähle als Itemname `Fackel`.
   * Es sollte ein Popup kommen, dass die Fackel nun auch in der Item-Bibliothek (`data/items/`) gespeichert wurde.
6. **Zustände hinzufügen:**
   * Scrolle zum Bereich `Zustände`.
   * Klicke auf `+ Neuer Zustand`.
   * Wähle als Name `Gute Laune`.
   * Vergib als Beschreibung `Der Charakter ist gut gelaunt`.
   * Wähle bei Auswirkung `keine Auswirkung`.
   * Belasse Ziel der Auswirkung auf `kein Ziel / n/a`
   * Lass den Modifikator leer
   * Klicke auf `Zustand speichern`
   * Es sollte ein Popup kommen, dass der Zustand nun auch in der Zustands-Bibliothek (`data/conditions/`) gespeichert wurde.
7. **Speichern:**
   * Klicke ganz unten auf den Button **Charakter Speichern**.
   * Bestätige eventuelle Info-Dialoge ("Charakter wurde gespeichert").

## Erwartetes Ergebnis
* Der Info-Dialog "Bestätigung" erscheint und meldet Erfolg.
* Liegt abhängig von der gewählten Kampagne ab: Ohne Kampagne liegt im Ordner `data/characters/` eine neue Datei. Mit Kampagne in `data/campaigns/<campaign_id>/`.
* Die JSON-Datei enthält alle oben eingetippten Schlüssel und Werte in der korrekten strukturellen Unterteilung (`hitpoints: 40`, `armor: { name: "Plattenpanzer", value: 5 }`, usw.).

## Cleanup
* Die neu erstellte Datei aus dem jeweiligen `data/`-Ordner im Backend löschen (sofern nicht mehr gebraucht).
