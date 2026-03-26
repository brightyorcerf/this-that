import psycopg2
import os
 
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:[YOUR-PASSWORD]@db.mtbsgadocmnhjxxdnmdj.supabase.co:5432/postgres")

def seed_to_supabase():
    IMAGE_DIR = "static/images"
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Create Table Structure Intelligently 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS girls (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE NOT NULL,
                elo INTEGER NOT NULL DEFAULT 1500
            );
        """)
         
        images = [f for f in os.listdir(IMAGE_DIR) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        
        print(f"Found {len(images)} images. Uploading...")

        for img in images: 
            cur.execute(
                "INSERT INTO girls (filename, elo) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (img, 1500) 
            )
            
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Successfully seeded {len(images)} images to Supabase!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    seed_to_supabase()