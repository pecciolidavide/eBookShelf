from flask import Flask, render_template, request, abort
import re
import os

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

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=1234, debug=True)
