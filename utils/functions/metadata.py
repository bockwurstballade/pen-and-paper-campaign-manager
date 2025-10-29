import os
import json

def load_all_characters_from_folder():
    """
    Liest alle gespeicherten Charaktere aus dem Ordner 'characters'
    und gibt eine Liste von Dicts zurück: 
    [ { "data": <char_dict>, "path": <pfad>, "display": <anzeigetext> }, ... ]
    """
    chars = []
    if not os.path.exists("characters"):
        return chars

    for fname in os.listdir("characters"):
        if fname.lower().endswith(".json"):
            full_path = os.path.join("characters", fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                char_name = data.get("name", "(unbenannt)")
                char_class = data.get("class", "?")
                char_age = data.get("age", "?")
                char_id = data.get("id", "???")
                display = f"{char_name} | {char_class}, {char_age} Jahre [{char_id[:8]}...]"

                chars.append({
                    "data": data,
                    "path": full_path,
                    "display": display,
                })
            except Exception:
                pass
    return chars