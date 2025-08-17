import os
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------
# Database config
# ---------------------
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))

ROOT = Path(__file__).resolve().parents[2]
CATEGORY_FILE = ROOT / "data_extraction" / "resources" / "category.txt"

# ---------------------
# DB helpers
# ---------------------
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        cursor_factory=RealDictCursor
    )

# ---------------------
# User and view creation
# ---------------------
def create_user(username):
    full_name = input("Enter your full name: ").strip()
    sex = input("Enter your sex (M/F/O): ").strip()
    occupation = input("Enter your occupation: ").strip()
    industry = input("Enter your industry: ").strip()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, name, sex, occupation, industry)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING user_id;
    """, (username, full_name, sex, occupation, industry))
    user_id = cur.fetchone()['user_id']
    conn.commit()
    cur.close()
    conn.close()
    print(f"User '{username}' created with ID {user_id}")
    return user_id

def create_default_view(user_id):
    print("\nSelect categories you want to learn (comma-separated numbers):\n")
    with open(CATEGORY_FILE, "r") as f:
        categories = [line.strip() for line in f if line.strip()]
    for i, c in enumerate(categories, 1):
        print(f"{i}. {c}")
    
    selection = input("\nYour choice: ").strip()
    indices = [int(x) - 1 for x in selection.split(",") if x.isdigit() and 0 <= int(x)-1 < len(categories)]
    selected_categories = [categories[i] for i in indices]

    description = input("Enter a brief description of what you want to learn: ").strip()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO views (user_id, name, description)
        VALUES (%s, 'default', %s)
        RETURNING view_id;
    """, (user_id, description))
    view_id = cur.fetchone()['view_id']

    for cat in selected_categories:
        cur.execute("""
            INSERT INTO view_categories (view_id, category)
            VALUES (%s, %s);
        """, (view_id, cat))
    
    conn.commit()
    cur.close()
    conn.close()
    print("Default view created.\n")
    return view_id

# ---------------------
# Recommendation logic
# ---------------------
def get_user_view(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT v.description, array_agg(vc.category) AS categories
        FROM views v
        JOIN view_categories vc ON v.view_id = vc.view_id
        WHERE v.user_id = %s AND v.name = 'default'
        GROUP BY v.description;
    """, (user_id,))
    view = cur.fetchone()
    cur.close()
    conn.close()
    return view

def get_candidate_posts(categories):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.guid, a.title, a.content, a.link
        FROM articles a
        JOIN categories c ON a.guid = c.article_guid
        WHERE c.category = ANY(%s)
        GROUP BY a.guid;
    """, (categories,))
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return posts

def rank_posts_by_relevance(user_description, posts):
    documents = [p['title'] + " " + p['content'] for p in posts]
    if not documents:
        return []

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    user_vector = vectorizer.transform([user_description])
    scores = cosine_similarity(user_vector, tfidf_matrix)[0]

    top_indices = scores.argsort()[::-1]
    ranked_posts = [posts[i] for i in top_indices]
    return ranked_posts

def get_recommended_posts(user_id, top_n=10):
    view = get_user_view(user_id)
    if not view:
        return []

    categories = view['categories']
    description = view['description']
    posts = get_candidate_posts(categories)
    ranked_posts = rank_posts_by_relevance(description, posts)
    return ranked_posts[:top_n]

# ---------------------
# Main CLI
# ---------------------
def main():
    username = input("Enter your username: ").strip()
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE username = %s;", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        user_id = create_user(username)
        create_default_view(user_id)
    else:
        user_id = user['user_id']

    recommended_posts = get_recommended_posts(user_id)
    if not recommended_posts:
        print("No recommended posts found for your categories.")
        return

    print("\nHere are your recommended posts:\n")
    for p in recommended_posts:
        print(f"Title: {p['title']}\nLink: {p['link']}\n")
    input("Press Enter to continue...")

if __name__ == "__main__":
    main()
