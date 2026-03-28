import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, flash, jsonify
from .helpers import updateElo
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
            
        cur.execute("SELECT total_votes FROM metadata WHERE id = 1")
        total_res = cur.fetchone()
        total_votes = total_res['total_votes'] if total_res and total_res['total_votes'] else 0
            
        cur.close()
        conn.close()
        return render_template("battle.html", MAX_ID=MAX_ID, girl1=girl1, girl2=girl2, girls=girls, total_votes=int(total_votes))
        
    else:  # POST request
        # Parse JSON if available, otherwise fallback to form
        data = request.get_json(silent=True) or request.form
        
        # Handle explicit pair ID requests conditionally passed inside the application 
        if data.get("id1") and data.get("id2"):
            id1 = data.get("id1")
            id2 = data.get("id2")
            
            # Security Audit: Stringent parsing over Python List Inclusion. Stops injection arrays natively
            try:
                id1 = int(id1)
                id2 = int(id2)
            except ValueError:
                cur.close()
                conn.close()
                return jsonify({"error": "Invalid image IDs selected: Must be integers"}), 400
            
            # Additional logical checks
            if id1 == id2 or id1 <= 0 or id2 <= 0:
                cur.close()
                conn.close()
                return jsonify({"error": "Invalid image IDs selected: IDs must be different and positive"}), 400
                
            cur.execute("SELECT id, filename, elo FROM girls WHERE id = %s", (id1,))
            girl1 = cur.fetchone()
            cur.execute("SELECT id, filename, elo FROM girls WHERE id = %s", (id2,))
            girl2 = cur.fetchone()
            
            cur.execute("SELECT total_votes FROM metadata WHERE id = 1")
            total_res = cur.fetchone()
            total_votes = total_res['total_votes'] if total_res and total_res['total_votes'] else 0
            
            cur.close()
            conn.close()
            
            if not girl1 or not girl2:
                return jsonify({"error": "Image IDs not found in database"}), 404
                
            return jsonify({
                "girl1": girl1,
                "girl2": girl2,
                "leaderboard": girls,
                "total_votes": int(total_votes)
            })
             
        elif data.get("winner") and data.get("loser"):
            try:
                winner_id = int(data.get("winner"))
                loser_id = int(data.get("loser")) 
                cur.execute("""
                    (SELECT id, filename, elo, 'battle' as type FROM girls WHERE id IN (%s, %s))
                    UNION ALL
                    (SELECT id, filename, elo, 'random' as type FROM girls WHERE id >= (SELECT floor(random() * (SELECT COALESCE(MAX(id), 0) FROM girls)) + 1) ORDER BY id LIMIT 2)
                    UNION ALL
                    (SELECT id, filename, elo, 'leader' as type FROM girls ORDER BY elo DESC LIMIT 3);
                """, (winner_id, loser_id))
                
                raw_results = cur.fetchall()
                 
                battle_data = {r['id']: r['elo'] for r in raw_results if r['type'] == 'battle'}
                next_randoms = [r for r in raw_results if r['type'] == 'random']
                leaderboard = [r for r in raw_results if r['type'] == 'leader']
 
                from .helpers import expected_score
                w_elo = battle_data.get(winner_id, 1200)
                l_elo = battle_data.get(loser_id, 1200)
                
                e_w = expected_score(w_elo, l_elo)
                e_l = expected_score(l_elo, w_elo)
                
                new_w = round(w_elo + 32 * (1 - e_w))
                new_l = round(l_elo + 32 * (0 - e_l))
 
                cur.execute("""
                    UPDATE girls SET elo = CASE 
                        WHEN id = %s THEN %s 
                        WHEN id = %s THEN %s 
                    END,
                    votes = COALESCE(votes, 0) + 1 
                    WHERE id IN (%s, %s);
                    
                    UPDATE metadata SET total_votes = total_votes + 1 WHERE id = 1 RETURNING total_votes;
                """, (winner_id, new_w, loser_id, new_l, winner_id, loser_id))
                
                total_votes = cur.fetchone()['total_votes'] or 0

                conn.commit()
                cur.close()
                conn.close()

                return jsonify({
                    "girl1": next_randoms[0] if len(next_randoms) > 0 else {"id":0, "filename":"err.jpg", "elo":1200},
                    "girl2": next_randoms[1] if len(next_randoms) > 1 else next_randoms[0],
                    "leaderboard": leaderboard,
                    "total_votes": int(total_votes)
                })

            except Exception as e:
                if conn: conn.rollback()
                return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)