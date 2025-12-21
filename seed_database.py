"""
Consolidated database setup script.
Run this once to create and populate your database.
"""
import sqlite3
import os

DB_PATH = "database.db"
IMAGE_DIR = "static/images"

def create_database():
    """Create the database schema using sqlite3"""
    
    # Check if database already exists
    if os.path.exists(DB_PATH):
        response = input(f"{DB_PATH} already exists. Overwrite? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            exit()
        os.remove(DB_PATH)
    
    # Create database with sqlite3 (CS50 requires file to exist first)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Create table
    cur.execute("""
        CREATE TABLE girls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            elo INTEGER NOT NULL DEFAULT 1500
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✓ Database schema created")

def seed_images():
    """Populate database with images from the images directory"""
    from cs50 import SQL
    
    db = SQL(f"sqlite:///{DB_PATH}")
    
    if not os.path.exists(IMAGE_DIR):
        print(f"✗ Error: {IMAGE_DIR} directory not found!")
        return
    
    images = [f for f in os.listdir(IMAGE_DIR) 
              if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
    
    if not images:
        print(f"✗ No images found in {IMAGE_DIR}")
        return
    
    for img in images:
        try:
            db.execute(
                "INSERT INTO girls (filename, elo) VALUES (?, ?)",
                img,
                1500
            )
        except Exception as e:
            print(f"✗ Error inserting {img}: {e}")
    
    print(f"✓ Seeded {len(images)} images with ELO rating of 1500")

def verify_database():
    """Verify the database was set up correctly"""
    from cs50 import SQL
    
    db = SQL(f"sqlite:///{DB_PATH}")
    count = db.execute("SELECT COUNT(*) as total FROM girls")[0]["total"]
    print(f"✓ Database contains {count} images")
    
    # Show sample
    if count > 0:
        sample = db.execute("SELECT id, filename, elo FROM girls LIMIT 3")
        print("\nSample entries:")
        for row in sample:
            print(f"  ID: {row['id']}, File: {row['filename']}, ELO: {row['elo']}")

if __name__ == "__main__":
    print("Setting up database...\n")
    
    create_database()
    seed_images()
    verify_database()
    
    print("\n✓ Setup complete! Run 'python app.py' to start the app.")