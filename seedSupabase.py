import psycopg2
import os
 
RAW_URL = os.environ.get("DATABASE_URL", "postgresql://postgres.mtbsgadocmnhjxxdnmdj:Ei4IvmIAjsU5lXra@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres")
DATABASE_URL = RAW_URL if "?" in RAW_URL else f"{RAW_URL}?sslmode=require"

def seed_to_supabase():
    IMAGE_DIR = "static/images"
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
         
        cur.execute("""
            CREATE TABLE IF NOT EXISTS girls (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE NOT NULL,
                elo INTEGER NOT NULL DEFAULT 1500
            );
        """)
 
        print("🧹 Wiping old database entries for a clean reseed...")
        cur.execute("TRUNCATE TABLE girls RESTART IDENTITY;")
          
        images = [f for f in os.listdir(IMAGE_DIR) 
                  if f.lower().endswith('.webp')]
        
        print(f"📂 Found {len(images)} compressed images. Uploading...")
 
        for img in images: 
            cur.execute(
                "INSERT INTO girls (filename, elo) VALUES (%s, %s)",
                (img, 1500) 
            )
            
        conn.commit()
        print(f"✅ Successfully synced {len(images)} images to Supabase!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    seed_to_supabase()