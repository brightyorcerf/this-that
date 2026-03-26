import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, flash
from helpers import updateElo
import secrets
import random

app = Flask(__name__, 
            template_folder="../templates", 
            static_folder="../static")

app.config["TEMPLATES_AUTO_RELOAD"] = True 
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))

def get_db_connection():
    """ Establish stateless Postgres Connection via Env Var """ 
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    return conn

def get_random_girl(cur):
    """
    O(1) approach for random fetching instead of ORDER BY random().
    ORDER BY random() forces a full table scan and database sort, killing scaling performance.
    Instead, we probabilistically leap into the ID space and take the first row we find.
    """
    cur.execute("""
        SELECT id, filename, elo 
        FROM girls 
        WHERE id >= (
            SELECT floor(random() * (SELECT COALESCE(MAX(id), 0) FROM girls)) + 1
        )
        ORDER BY id LIMIT 1;
    """)
    result = cur.fetchone()
    # Edge case due to massive gaps or if max random generation hits an empty pocket
    if not result:
        cur.execute("SELECT id, filename, elo FROM girls ORDER BY id LIMIT 1;")
        result = cur.fetchone()
    return result

def generate_random_pair(cur):
    """Generate two different random records"""
    girl1 = get_random_girl(cur)
    if not girl1:
        return None, None
        
    girl2 = get_random_girl(cur)
    
    # Deduplication retry limit in case of almost-empty database lengths
    retry_count = 0
    while girl2 and girl1['id'] == girl2['id'] and retry_count < 10:
        girl2 = get_random_girl(cur)
        retry_count += 1
        
    return girl1, girl2

@app.route("/", methods=["GET", "POST"])
def battle():
    try:
        conn = get_db_connection()
    except Exception as e:
        return f"Database connection failed: Make sure DATABASE_URL is set -> {e}", 500
        
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Leaderboard fetch
    cur.execute("SELECT id, filename, elo FROM girls ORDER BY elo DESC LIMIT 3")
    girls = cur.fetchall()
    
    cur.execute("SELECT MAX(id) AS counter FROM girls")
    count_res = cur.fetchone()
    MAX_ID = count_res['counter'] if count_res and count_res['counter'] else 0
    
    if request.method == "GET":
        girl1, girl2 = generate_random_pair(cur)
        if not girl1 or not girl2:
            girl1 = {"id": 0, "filename": "placeholder.jpg", "elo": 0}
            girl2 = {"id": 0, "filename": "placeholder.jpg", "elo": 0}
            
        cur.close()
        conn.close()
        return render_template("battle.html", MAX_ID=MAX_ID, girl1=girl1, girl2=girl2, girls=girls)
        
    else:  # POST request
        # Handle explicit pair ID requests conditionally passed inside the application 
        if request.form.get("id1") and request.form.get("id2"):
            id1 = request.form.get("id1")
            id2 = request.form.get("id2")
            
            # Security Audit: Stringent parsing over Python List Inclusion. Stops injection arrays natively
            try:
                id1 = int(id1)
                id2 = int(id2)
            except ValueError:
                flash("Invalid image IDs selected: Must be integers", "error")
                cur.close()
                conn.close()
                return redirect("/")
            
            # Additional logical checks
            if id1 == id2 or id1 <= 0 or id2 <= 0:
                flash("Invalid image IDs selected: IDs must be different and positive", "error")
                cur.close()
                conn.close()
                return redirect("/")
                
            cur.execute("SELECT id, filename, elo FROM girls WHERE id = %s", (id1,))
            girl1 = cur.fetchone()
            cur.execute("SELECT id, filename, elo FROM girls WHERE id = %s", (id2,))
            girl2 = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if not girl1 or not girl2:
                flash("Image IDs not found in database", "error")
                return redirect("/")
                
            return render_template("battle.html", MAX_ID=MAX_ID, girl1=girl1, girl2=girl2, girls=girls)
            
        # Standard Voting Path route
        elif request.form.get("winner") and request.form.get("loser"):
            winner_id = request.form.get("winner")
            loser_id = request.form.get("loser")
            
            # Security Audit Validation: Ensure they are parseable, unique integers!
            try:
                winner_id = int(winner_id)
                loser_id = int(loser_id)
            except ValueError:
                flash("Invalid vote format: IDs must be integer", "error")
                cur.close()
                conn.close()
                return redirect("/")
            
            if winner_id == loser_id or winner_id <= 0 or loser_id <= 0:
                flash("Invalid vote submission: self-votes not allowed", "error")
                cur.close()
                conn.close()
                return redirect("/")
                
            try:
                # Actual_Score is strictly passed internally as 1 (winner) and 0 (loser) 
                # resolving the strict actual_score inputs
                updateElo(winner_id, loser_id, conn, k_factor=32, actual_score_winner=1, actual_score_loser=0)
                conn.commit()
            except Exception as e:
                conn.rollback() # Ensure transaction closes properly to avoid locks!
                flash(f"Error recording vote: {str(e)}", "error")
                cur.close()
                conn.close()
                return redirect("/")
                
            # AUTO-GENERATE NEXT PAIR
            girl1, girl2 = generate_random_pair(cur)
            if girl1 and girl2:
                cur.execute("SELECT id, filename, elo FROM girls ORDER BY elo DESC LIMIT 3")
                girls = cur.fetchall()
                cur.close()
                conn.close()
                return render_template("battle.html", MAX_ID=MAX_ID, girl1=girl1, girl2=girl2, girls=girls)
            else:
                cur.close()
                conn.close()
                return redirect("/")
                
        else:
            cur.close()
            conn.close()
            return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)