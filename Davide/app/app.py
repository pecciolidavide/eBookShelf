from flask import Flask, render_template, request, abort, redirect, url_for
import re
import os
import base64

app = Flask(__name__)

def parse_org_db(file_path="database.org"):
    books = []
    if not os.path.exists(file_path):
        return books

    current_section = "Sconosciuta"
    current_book = None
    text_mode = None

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            if stripped.startswith("* "):
                current_section = stripped[2:].strip()

            elif stripped.startswith("** "):
                if current_book:
                    books.append(current_book)

                title_tags = stripped[3:].strip()
                parts = [p for p in title_tags.split(':') if p]
                title = parts[0].strip() if parts else title_tags
                tags_list = [t.strip() for t in parts[1:]] if len(parts) > 1 else []

                current_book = {
                    "id": len(books),
                    "section": current_section,
                    "title": title,
                    "tags": tags_list,
                    "author": "Ignoto",
                    "insert_date": "",
                    "format": "fisico",
                    "cover_png": "",
                    "width": 5,
                    "rating": 0.0,
                    "description": "",
                    "review": ""
                }
                text_mode = None

            elif stripped.startswith(":PROPERTIES:") or stripped.startswith(":END:"):
                continue

            elif stripped.startswith(":") and current_book and not text_mode:
                match = re.match(r':([A-Z_]+):\s*(.*)', stripped)
                if match:
                    key, val = match.groups()
                    key = key.lower()
                    if key == "width":
                        current_book[key] = int(val) if val.isdigit() else 5
                    elif key == "rating":
                        try:
                            current_book[key] = float(val)
                        except ValueError:
                            current_book[key] = 0.0
                    else:
                        current_book[key] = val.strip()

            elif stripped.startswith("*** "):
                if "Descrizione" in stripped:
                    text_mode = "description"
                elif "Recensione" in stripped:
                    text_mode = "review"

            elif text_mode and current_book:
                if line.strip() != "":
                    current_book[text_mode] += line + "<br>"

        if current_book:
            books.append(current_book)

    books.sort(key=lambda x: x["title"].lower())
    return books

def update_cover_in_db(book_id, file_storage, file_path="database.org"):
    if not file_storage or file_storage.filename == "":
        return False

    try:
        mime_type = file_storage.mimetype
        # Converte il file caricato in formato stringa BASE 64
        base64_data = base64.b64encode(file_storage.read()).decode('utf-8')
        # Crea l'URI dei dati standard per HTML
        data_uri = f"data:{mime_type};base64,{base64_data}"
    except Exception:
        return False

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_index = -1
    in_target_book = False
    in_properties = False
    updated = False

    new_lines = []

    for line in lines:
        stripped = line.strip()

        # Identifica il libro in base all'ordine di parsing
        if stripped.startswith("** "):
            current_index += 1
            if current_index == book_id:
                in_target_book = True
            else:
                in_target_book = False

        if in_target_book:
            if stripped == ":PROPERTIES:":
                in_properties = True
                new_lines.append(line)
                continue

            if in_properties:
                if stripped.startswith(":COVER_PNG:"):
                    # Sostituisce la riga esistente della copertina
                    new_lines.append(f":COVER_PNG: {data_uri}\n")
                    updated = True
                    continue
                elif stripped == ":END:":
                    if not updated:
                        # Inserisce la voce se non esisteva in precedenza
                        new_lines.append(f":COVER_PNG: {data_uri}\n")
                        updated = True
                    in_properties = False

        new_lines.append(line)

    # Riscrive il database con il dato aggiornato
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return True

@app.route("/")
def index():
    books = parse_org_db()
    return render_template("index.html", books=books)

@app.route("/book/<int:book_id>")
def book_detail(book_id):
    books = parse_org_db()
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        abort(404)
    return render_template("detail.html", book=book)

@app.route("/upload_cover/<int:book_id>", methods=["POST"])
def upload_cover(book_id):
    if "cover_image" not in request.files:
        return redirect(url_for("book_detail", book_id=book_id))

    file_storage = request.files["cover_image"]
    update_cover_in_db(book_id, file_storage)

    return redirect(url_for("book_detail", book_id=book_id))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=1234, debug=True)
