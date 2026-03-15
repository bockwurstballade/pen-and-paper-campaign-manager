# UI-Test-Matrix: Items & Edge Cases

Diese Matrix definiert verschiedene Testfälle für Randbedingungen und Fehlerzustände bezüglich der Item-Verwaltung.

| ID | Test-Kategorie | Szenario | Erwartetes Verhalten / Fehler-Handling | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-ITEM-01** | **Speichern** | *Leerer Name*<br>Der Nutzer klickt auf Speichern, hat aber das Namensfeld komplett leer gelassen. | Das Item wird mit einem Fallback-Namen wie "Unbenannt" gespeichert, die App stürzt nicht ab. | ⬜ |
| **TC-ITEM-02** | **Update** | *Bestehendes Item aktualisieren*<br>Ein Item `Fackel` (mit UUID X) wird im Editor geladen, der Name wird zu `Brennende Fackel` geändert und wieder gespeichert. | Die alte Datei `Fackel - X.json` wird gelöscht/überschrieben, und stattdessen existiert nun `Brennende Fackel - X.json`. | ⬜ |
| **TC-ITEM-03** | **Duplikate** | *Zweimal der gleiche Name*<br>Der Nutzer erstellt manuell ein völlig neues Item (neue UUID), das exakt so heißt wie ein bereits in `data/items/` existierendes Item. | Beide Dateien existieren friedlich nebeneinander, da sie sich in der UUID unterscheiden (z.B. `Seil - UUID1.json` und `Seil - UUID2.json`). | ⬜ |
| **TC-ITEM-04** | **Laden (Korrupt)** | *Korruptes JSON in `data/items/`*<br>Eine JSON-Datei in `data/items/` wurde manuell editiert und hat Syntax-Fehler. | Der `DataManager.get_all_items()` fängt den Fehler per `Exception` (und Logger) ab. Das fehlerhafte Item wird ignoriert, die restlichen Items laden normal. | ⬜ |
| **TC-ITEM-05** | **Verlinkung** | *Zustand verlinken, der nicht existiert*<br>Ein Item verweist auf eine `cond_id`, für die es in `data/conditions/` keine Datei gibt. | Das Laden des Items führt nicht zum Absturz. Das Fehlen des Zustands wird entweder später im Charakterbogen aufgefangen oder stillschweigend ignoriert. | ⬜ |
| **TC-ITEM-06** | **Zeichen im Namen** | *Sonderzeichen im Namen*<br>Das Item heißt `Schwert / Axt (Magisch) & "+1"`. | Der `DataManager` bereinigt den Dateinamen (z.B. `Schwert  Axt Magisch  1.json`), sodass das Betriebssystem keinen `OSError` wegen ungültiger Dateipfade wirft. | ⬜ |

### Anleitung zur Benutzung
Wenn du einen dieser Tests durchführst, setze den Status auf `✅`, falls er erfolgreich durchläuft, oder auf `❌`, falls die Anwendung dort unerwartet abstürzt oder ein Fehlverhalten aufweist. Hinterlege im Fehlerfall ein kurzes Issue im Root-Verzeichnis.
