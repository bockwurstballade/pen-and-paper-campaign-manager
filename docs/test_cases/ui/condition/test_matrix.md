# UI-Test-Matrix: Zustände & Edge Cases

Diese Matrix definiert verschiedene Testfälle für Randbedingungen und Fehlerzustände bezüglich der Zustands-Verwaltung.

| ID | Test-Kategorie | Szenario | Erwartetes Verhalten / Fehler-Handling | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-COND-01** | **Speichern** | *Leerer Name*<br>Der Nutzer klickt auf Speichern, lässt aber den Namen leer. | Fallback-Name "Unbenannt" wird verwendet, kein UI-Absturz. | ⬜ |
| **TC-COND-02** | **Update** | *Bestehenden Zustand aktualisieren*<br>Der Zustand `Blutend` wird umbenannt in `Schwer Blutend` und gespeichert. | Die Datei `Blutend - UUID.json` verschwindet, stattdessen existiert nun `Schwer Blutend - UUID.json`. | ⬜ |
| **TC-COND-03** | **Laden (Typen)** | *Falscher Datentyp im Modifikator*<br>Der Nutzer gibt statt `-5` das Wort `fünf` im Modifikator-Feld ein. | Die UI wirft ein lesbares Popup ("Der Modifikator muss eine ganze Zahl sein") und bricht den Speichervorgang ab. | ⬜ |
| **TC-COND-04** | **Laden (Korrupt)** | *Korruptes JSON in `data/conditions/`*<br>Eine JSON-Datei in `data/conditions/` wurde manuell editiert und hat Syntax-Fehler. | Der `DataManager.get_all_conditions()` loggt den Fehler, ignoriert diesen Zustand und lädt die restlichen Dateien fehlerfrei weiter. | ⬜ |
| **TC-COND-05** | **Duplikate** | *Zwei gleichnamige Zustände*<br>Manuelles Erstellen von 2x `Vergiftet` (unterschiedliche UUIDs). | Dateien existieren problemlos parallel im Dateisystem. (Beim Zuweisen auf einen Charakter muss ggf. durch die UUID differenziert werden, Abstürze gibt es aber nicht.) | ⬜ |
| **TC-COND-06** | **Bereinigung** | *Betriebssystem-feindlicher Name*<br>Der Zustand heißt `Slash / Backslash \ & ?`. | Der `DataManager` filtert den Namen für den Dateisystemaufruf (z. B. `Slash  Backslash    - UUID.json`), verhindert so `OSErrors`. | ⬜ |

### Anleitung zur Benutzung
Wenn du einen dieser Tests durchführst, setze den Status auf `✅`, falls er erfolgreich durchläuft, oder auf `❌`, falls die Anwendung dort unerwartet abstürzt oder ein Fehlverhalten aufweist. Hinterlege im Fehlerfall ein kurzes Issue im Root-Verzeichnis.
