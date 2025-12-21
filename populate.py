from cs50 import SQL 
import os

db = SQL("sqlite:///database.db")

images = os.listdir("static/images")
for img in images:
    db.execute(
        "INSERT INTO girls (filename, elo) VALUES (?, ?)",
        img,
        1500
    )
