import psycopg2
from psycopg2.extras import RealDictCursor

def updateElo(winner_id, loser_id, conn, k_factor=32, actual_score_winner=1, actual_score_loser=0):
    """
    Update ELO ratings for winner and loser using proper transactions.
    
    Args:
        winner_id: ID of the winning image
        loser_id: ID of the losing image
        conn: PostgreSQL connection object
        k_factor: ELO K-factor (default 32)
        actual_score_winner: Required strict validation, 1 for winning
        actual_score_loser: Required strict validation, 0 for loser
    
    Returns:
        tuple: (new_winner_elo, new_loser_elo)
    """
    # Strict validation of Actual_Score inputs securely
    if actual_score_winner not in (0, 0.5, 1) or actual_score_loser not in (0, 0.5, 1):
        raise ValueError("Invalid Actual_Score input. Must be 0, 0.5, or 1.")
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Fetch current ratings using strictly parameterized queries to prevent SQL injections
            cur.execute("SELECT elo FROM girls WHERE id = %s", (int(winner_id),))
            winner = cur.fetchone()
            
            cur.execute("SELECT elo FROM girls WHERE id = %s", (int(loser_id),))
            loser = cur.fetchone()
            
            if not winner or not loser:
                raise ValueError("Invalid Player ID: User does not exist in DB.")
            
            winner_elo = winner["elo"]
            loser_elo = loser["elo"]
            
            # Calculate expected scores
            expected_winner = expected_score(winner_elo, loser_elo)
            expected_loser = expected_score(loser_elo, winner_elo)
            
            # Calculate new ratings using the strictly validated actual scores
            new_winner_elo = round(winner_elo + k_factor * (actual_score_winner - expected_winner))
            new_loser_elo = round(loser_elo + k_factor * (actual_score_loser - expected_loser))
            
            # Update database safely
            cur.execute("UPDATE girls SET elo = %s WHERE id = %s", (new_winner_elo, int(winner_id)))
            cur.execute("UPDATE girls SET elo = %s WHERE id = %s", (new_loser_elo, int(loser_id)))
            
        return new_winner_elo, new_loser_elo
        
    except Exception as e:
        raise e

def expected_score(rating_a, rating_b):
    """
    Calculate expected score in ELO system using the logistic formula.
    Safely bounded to prevent precision loss or Overflow Errors due to massive rating discrepancies.
    """
    exponent = (rating_b - rating_a) / 400.0
    
    # Cap exponent extremes. 10^40 is an absurdly huge number. Anything > 10 is 99.99%+ skewed probability.
    # Prevents math OverflowError when ELOs diverge pathologically.
    if exponent > 40:
        return 0.0
    elif exponent < -40:
        return 1.0
        
    return 1.0 / (1.0 + 10.0 ** exponent)