# UI-Testfall: 02 - Charakter laden und anzeigen

## Ziel
Sicherstellen, dass ein bereits vorhandener Charakter (inklusive aller seiner tiefen Strukturen wie Items, Zustände, Fähigkeiten und Rüstung) korrekt aus der JSON-Datei gelesen und visuell richtig in den UI-Komponenten des Erstellungs-Dialogs abgebildet wird.

## Voraussetzungen
* Die Applikation ist gestartet (`python3 campaign-manager.py`).
* Es existiert ein bekannter Test-Charakter im Ordner `data/characters/` oder in einem Kampagnen-Ordner. (Falls nicht, führe Testfall `01_character_creation.md` vorher aus).
* Der Test-Charakter hat mindestens:
  * Einen Namen, definierte HP und Alter.
  * Einen Rüstungswert > 0.
  * Mindestens einen Skill und einen Kategorie-Wert.
  * Mindestens 1 Item im Inventar.
  * Mindestens 1 manuell angelegten Zustand.

## Ablauf

1. **Start:** Klicke im Hauptfenster auf **Bestehenden Charakter laden**.
2. **Laden auslösen:**
   * Nutze das Dropdown-Menü ganz oben ("Bestehenden Charakter laden").
   * Klicke auf den Dropdown-Pfeil und wähle den zuvor erstellten Charakter (z.B. `Arthas | Gärtner | 35 Jahre`) aus.
3. **Überprüfung Base Stats:**
   * Prüfe, ob "Name", "Klasse", "Lebenspunkte" und "Grundschaden" korrekt in die entsprechenden Textfelder der UI übernommen wurden.
4. **Überprüfung Rüstung:**
   * Prüfe, ob die Checkbox "Charakter trägt Rüstung" angehakt ist.
   * Prüfe, ob "Rüstungsname" und "Rüstungswert" korrekt befüllt sind.
5. **Überprüfung Fähigkeiten:**
   * Scrolle nach unten zum Bereich "Fähigkeiten & Attribute".
   * Klicke den Tab "Handeln" (oder den Tab, in dem Werte stehen).
   * Verifiziere, dass der Basiswert und der Wert für den spezifischen Skill (z. B. "Schlösser knacken") wieder die Zahl `10` bzw. `5` anzeigen.
   * *Achtung:* Auch die berechneten Endpunkt-Labels (Base + Skill) sollten korrekt aktualisiert sein (z.B. `15`).
6. **Überprüfung Items:**
   * Prüfe, ob das Layout für das/die Item(s) generiert wurde (z.B. eine GroupBox mit dem Namen "Fackel").
7. **Überprüfung Zustände:**
   * Gehe zum Abschnitt "Zustände".
   * Prüfe, ob der zuvor definierte Zustand (z.B. "Gute Laune") mit allen Detailtexten im Layout vorhanden ist.

## Erwartetes Ergebnis
* Die Anwendung darf beim Umschalten des Dropdown-Menüs **nicht abstürzen** (keine `AttributeError`s).
* Jedes UI-Element wird visuell auf den Stand der JSON-Datei aktualisiert.
* Manuelle Änderungen (z.B. das Hinzufügen einer zweiten Rüstung) überschreiben die Anzeige, bis man erneut etwas anderes lädt oder speichert.

## Cleanup
* Keine speziellen Aufräumarbeiten nötig, solange "Speichern" nicht gedrückt wurde.
