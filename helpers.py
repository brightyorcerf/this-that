def updateElo(winnerId, loserId, db):
    try:
        db.execute("BEGIN")
        winner = db.execute(
            "SELECT elo FROM girls WHERE id = ?", int(winnerId)
        )
        loser = db.execute(
            "SELECT elo FROM girls WHERE id = ?", int(loserId)
        )

        if not winner or not loser:
            raise ValueError("Invalid Player Id")

        winnerElo = winner[0]["elo"]
        loserElo = loser[0]["elo"]

        expectedWinner = expectedScore(winnerElo, loserElo)
        expectedLoser = expectedScore(loserElo, winnerElo)

        newWinnerElo = round(winnerElo + 100 * (1 - expectedWinner))
        newLoserElo = round(loserElo + 100 * (0 - expectedLoser))

        db.execute(
            "UPDATE girls SET elo = ? WHERE id = ?", newWinnerElo, winnerId
        )

        db.execute(
            "UPDATE girls SET elo = ? WHERE id = ?", newLoserElo, loserId
        )

        db.execute("COMMIT")

    except Exception:
        db.execute("ROLLBACK")
        raise 

def expectedScore(ratingA, ratingB):
    return 1/(1 + 10**((ratingB - ratingA)/400))