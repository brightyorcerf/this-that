import psycopg2
import os

RAW_URL = os.environ.get("DATABASE_URL", "postgresql://postgres.mtbsgadocmnhjxxdnmdj:Ei4IvmIAjsU5lXra@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres")
DATABASE_URL = RAW_URL if "?" in RAW_URL else f"{RAW_URL}?sslmode=require"

def init_metadata():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            id INT PRIMARY KEY,
            total_votes INT DEFAULT 0
        );
        INSERT INTO metadata (id, total_votes) 
        VALUES (1, COALESCE((SELECT SUM(votes)/2 FROM girls), 0)) 
        ON CONFLICT (id) DO NOTHING;
    """)
    conn.commit()
    print("Metadata table created and seeded successfully!")
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_metadata()
