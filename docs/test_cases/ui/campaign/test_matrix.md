# UI-Test-Matrix: Kampagnen-Management Edge Cases

Diese Matrix definiert verschiedene Testfälle für Randbedingungen (Edge Cases) und Fehlerzustände bezüglich der Kampagnenverwaltung.

| ID | Test-Kategorie | Szenario | Erwartetes Verhalten / Fehler-Handling | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-CAMP-01** | **Speichern** | *Fehlender Titel*<br>Der Nutzer lässt das Feld "Titel" leer und klickt auf "Speichern". | Ein Warn-Popup ("Bitte einen Titel für die Kampagne eingeben.") erscheint. Die Kampagne wird nicht gespeichert, und der Dialog bleibt offen. | ⬜ |
| **TC-CAMP-02** | **Speichern** | *Sonderzeichen im Titel*<br>Der Nutzer gibt als Titel `<Kampagne?!>` ein.* | Der `DataManager` filtert die invaliden Dateisystem-Zeichen heraus (`<`, `>`, `?`, `!`) und formatiert den Dateinamen sicher als `Kampagne - [UUID].json`. Es kommt zu keinem Systemabsturz. | ⬜ |
| **TC-CAMP-03** | **Laden (Vorbereitung)** | *Manipulierte JSON-Datei laden*<br>Eine Kampagnendatei in `data/campaigns` wird im Editor so modifiziert, dass das JSON-Format invalid ist (z.B. fehlende geschweifte Klammer). | (Sobald Kampagnenauswahl implementiert ist) Das System loggt einen Fehler, ignoriert die Datei fehlerfrei und stürzt nicht ab. | ⬜ |
| **TC-CAMP-04** | **Regelwerk** | *Leeres Regelwerk*<br>Das Feld "Regelwerk" wird leer gelassen. | Kein Problem, Kampagne kann erfolgreich auch mit leerem Regelwerk-Feld gespeichert werden. | ⬜ |

### Anleitung zur Benutzung
Setze den Status nach einem Testdurchlauf auf `✅` (Erfolg) oder `❌` (Fehlschlag). Tritt bei einem Test ein Fehlschlag oder Crash `Aborted (core dumped)` auf, öffne ein Issue oder korrigiere das Fehler-Handling entsprechend.
