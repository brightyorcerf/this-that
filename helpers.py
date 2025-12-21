def updateElo(winner_id, loser_id, db, k_factor=32):
    """
    Update ELO ratings for winner and loser using proper transactions.
    
    Args:
        winner_id: ID of the winning image
        loser_id: ID of the losing image
        db: Database connection object
        k_factor: ELO K-factor (default 32, standard rating)
                  Use 40-50 for faster convergence, 16-24 for slower
    
    Returns:
        tuple: (new_winner_elo, new_loser_elo)
    
    Raises:
        ValueError: If invalid player IDs provided
        Exception: If database transaction fails
    """
    try:
        db.execute("BEGIN TRANSACTION")
        
        # Fetch current ratings
        winner = db.execute("SELECT elo FROM girls WHERE id = ?", int(winner_id))
        loser = db.execute("SELECT elo FROM girls WHERE id = ?", int(loser_id))
        
        if not winner or not loser:
            raise ValueError("Invalid Player ID")
        
        winner_elo = winner[0]["elo"]
        loser_elo = loser[0]["elo"]
        
        # Calculate expected scores
        expected_winner = expected_score(winner_elo, loser_elo)
        expected_loser = expected_score(loser_elo, winner_elo)
        
        # Calculate new ratings
        # Winner gets: current + K * (actual_score - expected_score)
        # actual_score = 1 for winner, 0 for loser
        new_winner_elo = round(winner_elo + k_factor * (1 - expected_winner))
        new_loser_elo = round(loser_elo + k_factor * (0 - expected_loser))
        
        # Update database
        db.execute("UPDATE girls SET elo = ? WHERE id = ?", new_winner_elo, int(winner_id))
        db.execute("UPDATE girls SET elo = ? WHERE id = ?", new_loser_elo, int(loser_id))
        
        db.execute("COMMIT")
        
        return new_winner_elo, new_loser_elo
        
    except Exception as e:
        db.execute("ROLLBACK")
        raise e


def expected_score(rating_a, rating_b):
    """
    Calculate expected score in ELO system using the logistic formula.
    
    The expected score represents the probability that player A will win
    against player B based on their current ratings.
    
    Args:
        rating_a: ELO rating of player A
        rating_b: ELO rating of player B
    
    Returns:
        float: Expected score (probability between 0 and 1)
               - 0.5 means equal chance
               - 0.75 means 75% chance player A wins
               - 0.25 means 25% chance player A wins
    
    Example:
        >>> expected_score(1600, 1600)
        0.5
        >>> expected_score(1700, 1600)  
        0.64  # Higher rated player has ~64% chance to win
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))