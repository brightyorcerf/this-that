from cs50 import SQL
from flask import Flask, render_template, request, redirect, flash
from helpers import updateElo
import secrets
import random

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = secrets.token_hex(16)  # For flash messages

db = SQL("sqlite:///database.db")

def get_max_id():
    """Get the maximum ID from the database"""
    result = db.execute("SELECT COUNT(id) as counter FROM girls")
    return result[0]["counter"] if result else 0

def generate_random_pair(max_id):
    """Generate two different random IDs"""
    if max_id < 2:
        return None, None
    
    id1 = random.randint(1, max_id)
    id2 = random.randint(1, max_id)
    
    while id1 == id2:
        id2 = random.randint(1, max_id)
    
    return id1, id2

@app.route("/", methods=["GET", "POST"])
def battle():
    MAX_ID = get_max_id()
    
    # Get TOP 3 leaderboard data only
    girls = db.execute("SELECT id, filename, elo FROM girls ORDER BY elo DESC LIMIT 3")
    
    if request.method == "GET":
        # Auto-generate a random pair on initial load
        id1, id2 = generate_random_pair(MAX_ID)
        
        if id1 and id2:
            girl1 = db.execute("SELECT id, filename, elo FROM girls WHERE id = ?", id1)[0]
            girl2 = db.execute("SELECT id, filename, elo FROM girls WHERE id = ?", id2)[0]
        else:
            # Fallback if not enough images
            girl1 = {"id": 0, "filename": "placeholder.jpg", "elo": 0}
            girl2 = {"id": 0, "filename": "placeholder.jpg", "elo": 0}
        
        return render_template("battle.html", MAX_ID=MAX_ID, girl1=girl1, girl2=girl2, girls=girls)
    
    else:  # POST request
        # Handle pair generation request
        if request.form.get("id1") and request.form.get("id2"):
            id1 = request.form.get("id1")
            id2 = request.form.get("id2")
            
            # Validation
            valid_ids = [str(x) for x in range(1, MAX_ID + 1)]
            if id1 not in valid_ids or id2 not in valid_ids or id1 == id2:
                flash("Invalid image IDs selected", "error")
                return redirect("/")
            
            # Fetch girls with filename
            girl1 = db.execute("SELECT id, filename, elo FROM girls WHERE id = ?", int(id1))[0]
            girl2 = db.execute("SELECT id, filename, elo FROM girls WHERE id = ?", int(id2))[0]
            
            return render_template("battle.html", MAX_ID=MAX_ID, girl1=girl1, girl2=girl2, girls=girls)
        
        # Handle vote submission - AUTO-GENERATE NEXT PAIR
        elif request.form.get("winner") and request.form.get("loser"):
            winner_id = request.form.get("winner")
            loser_id = request.form.get("loser")
            
            # Validation
            valid_ids = [str(x) for x in range(1, MAX_ID + 1)]
            if winner_id not in valid_ids or loser_id not in valid_ids or winner_id == loser_id:
                flash("Invalid vote submission", "error")
                return redirect("/")
            
            # Update ELO ratings
            try:
                updateElo(winner_id, loser_id, db)
            except Exception as e:
                flash(f"Error recording vote: {str(e)}", "error")
                return redirect("/")
            
            # AUTO-GENERATE NEXT PAIR instead of redirecting
            id1, id2 = generate_random_pair(MAX_ID)
            
            if id1 and id2:
                girl1 = db.execute("SELECT id, filename, elo FROM girls WHERE id = ?", id1)[0]
                girl2 = db.execute("SELECT id, filename, elo FROM girls WHERE id = ?", id2)[0]
                
                # Refresh leaderboard (in case top 3 changed)
                girls = db.execute("SELECT id, filename, elo FROM girls ORDER BY elo DESC LIMIT 3")
                
                return render_template("battle.html", MAX_ID=MAX_ID, girl1=girl1, girl2=girl2, girls=girls)
            else:
                return redirect("/")
        
        else:
            # Invalid POST request
            return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)