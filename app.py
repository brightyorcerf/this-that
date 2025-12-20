from cs50 import SQL
from flask import Flask, render_template, request, redirect
from helpers import updateElo

app = Flask(__name__)
app.config ["TEMPLATES_AUTO_RELOAD"] = True

db = SQL("sqlite:///database.db")

MAX_ID = db.execute("SELECT COUNT(id) as counter from girls")[0]["counter"] 

# on load redirect to battle 
@app.route("/", methods = ["GET", "POST"])
def battle():

    girls = db.execute("SELECT id, elo FROM girls ORDER BY elo DESC")

    # generate IDs
    if request.method == "GET":
        girl1 = {"id": 0, "name": "emma", "elo": None}
        girl2 = {"id": 0, "name": "anne", "elo": None}
        return render_template("battle.html", MAX_ID=MAX_ID, girl1=girl1, girl2=girl2, girls=girls)

    else:
        #if generation request 
        if request.form.get("id1") != None and request.form.get("id2") != None:
            id1 = request.form.get("id1")
            id2 = request.form.get("id2")

            # validation step 
            if not id1 in [str(x) for x in range(1, MAX_ID + 1)] or not id2 in [str(x) for x in range(1, MAX_ID+1)] or id1 == id2:
                return redirect("/")

            girl1 = db.execute("SELECT id, elo FROM girls WHERE id = ?", int(id1))[0]
            girl2 = db.execute("SELECT id, elo FROM girls WHERE id = ?", int(id2))[0]     

            return render_template("battle.html", MAX_ID=MAX_ID, girl1=girl1, girl2=girl2, girls=girls)  

        # if elo change req
        elif  request.form.get("winner") != None and request.form.get("loser") != None:

            winnerId = request.form.get("winner")
            loserId = request.form.get("loser")

            if not winnerId in [str(x) for x in range(1, MAX_ID + 1)] or not loserId in [str(x) for x in range(1, MAX_ID+1)] or winnerId == loserId:
                    return redirect("/")

            updateElo(winnerId, loserId, db) # update elo 

            return redirect("/") # generate new IDs

        else:
            #generate new IDs
            return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)    