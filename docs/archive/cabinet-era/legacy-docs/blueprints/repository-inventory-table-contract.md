# Repository-Inventory-Tabellencontract

Die zweispaltigen Metadatentabellen in `Repository Reference.md` bleiben strikt fail-closed.

- Ein Pipe-Zeichen innerhalb eines Tabellenwertes muss mit einem unmittelbar vorangestellten Backslash escaped werden.
- Eine ungerade Zahl unmittelbar vorangehender Backslashes escaped das Pipe-Zeichen; genau ein Escape-Backslash wird beim Parsen entfernt.
- Bei einer geraden Zahl vorangehender Backslashes bleibt das Pipe-Zeichen ein Spaltentrenner.
- Rohe zusätzliche Pipe-Zeichen erzeugen zusätzliche Zellen und sind ein Contractfehler.
- Diese Regel gilt auch innerhalb von Inline-Code in einer Tabellenzelle.

Der Generator implementiert damit bewusst nur den benötigten deterministischen Zweispalten-Contract und keinen allgemeinen Markdown-Parser.
