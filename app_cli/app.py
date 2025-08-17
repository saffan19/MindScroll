import os
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))

ROOT = Path(__file__).resolve().parents[1]
CATEGORY_FILE = ROOT / "data_extraction" / "resources" / "categories.txt"

# ---------------------
# DB helpers
# ---------------------
def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def load_categories():
    with open(CATEGORY_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def user_exists(conn, username):
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        return row[0] if row else None

def create_user(conn, username):
    full_name = input("Full Name: ").strip()
    sex = input("Sex (M/F/Other): ").strip()
    occupation = input("Occupation: ").strip()
    industry = input("Industry: ").strip()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO users (username, name, sex, occupation, industry)
            VALUES (%s, %s, %s, %s, %s) RETURNING user_id
        """, (username, full_name, sex, occupation, industry))
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id

# ---------------------
# Default view creation
# ---------------------
def create_default_view(conn, user_id, ask_categories=True):
    all_categories = load_categories()
    selected_categories = []

    if ask_categories:
        print("\nSelect categories you want to learn (press 'n' to finish):")
        while True:
            remaining_categories = [c for c in all_categories if c not in selected_categories]
            if not remaining_categories:
                break
            for i, cat in enumerate(remaining_categories, 1):
                print(f"{i}. {cat}")
            selection = input("Enter numbers (comma-separated) or 'n' to finish: ").strip()
            if selection.lower() == 'n':
                break
            indices = [int(x.strip()) - 1 for x in selection.split(",") if x.strip().isdigit()]
            for i in indices:
                if 0 <= i < len(remaining_categories):
                    selected_categories.append(remaining_categories[i])

    description = "Default view for your learning preferences" if not ask_categories else input("Enter a brief description of what you want to learn: ").strip()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO views (user_id, name, description)
            VALUES (%s, 'default', %s) RETURNING view_id
        """, (user_id, description))
        view_id = cur.fetchone()[0]

        if selected_categories:
            values = [(view_id, cat) for cat in selected_categories]
            execute_values(cur, "INSERT INTO view_categories (view_id, category) VALUES %s", values)
        conn.commit()
    return view_id, description

# ---------------------
# Recommendation logic
# ---------------------
def get_posts_for_view(conn, view_id):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT a.guid,
                   llm.title AS llm_title,
                   llm.content AS llm_content,
                   vc.category
            FROM view_categories vc
            JOIN categories c
              ON vc.category = c.category
            JOIN articles a
              ON a.guid = c.article_guid
            JOIN llm_content llm
              ON llm.article_guid = a.guid
            WHERE vc.view_id = %s
            GROUP BY a.guid, llm.title, llm.content, vc.category
        """, (view_id,))
        return cur.fetchall()
def get_default_view(conn, user_id):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT view_id, description
            FROM views
            WHERE user_id = %s AND name = 'default'
            LIMIT 1
        """, (user_id,))
        row = cur.fetchone()
        if row:
            return row['view_id'], row['description']
        return None, None
def rank_posts(description, posts):
    if not posts:
        return []
    documents = [p['llm_title'] + " " + p['llm_content'] for p in posts]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    user_vector = vectorizer.transform([description])
    scores = cosine_similarity(user_vector, tfidf_matrix)[0]
    return [posts[i] for i in scores.argsort()[::-1]]

# ---------------------
# Display posts one by one
# ---------------------
def show_posts(conn, view_id, description):
    posts = get_posts_for_view(conn, view_id)
    ranked_posts = rank_posts(description, posts)

    if not ranked_posts:
        print("\nNo posts found for your selected categories.\n")
        return

    i = 0
    while i < len(ranked_posts):
        post = ranked_posts[i]
        print(f"\nTitle: {post['llm_title']}\nContent: {post['llm_content']}\n")
        action = input("Press 'n' for next, 'e' to exit: ").strip().lower()
        if action == 'e':
            break
        elif action == 'n':
            try:
                seconds = int(input("Seconds viewed: "))
                liked = int(input("Liked? (1=yes, 0=no): "))
            except ValueError:
                seconds, liked = 0, 0

            # Update view_tag_interactions
            # with conn.cursor() as cur:
            #     cur.execute("SELECT category FROM view_categories WHERE view_id = %s", (view_id,))
            #     tags = [r[0] for r in cur.fetchall()]
            #     for tag in tags:
            #         cur.execute("""
            #             INSERT INTO view_tag_interactions (view_id, tag, seconds_viewed, liked)
            #             VALUES (%s, %s, %s, %s)
            #             ON CONFLICT (view_id, tag) DO UPDATE
            #             SET seconds_viewed = view_tag_interactions.seconds_viewed + EXCLUDED.seconds_viewed,
            #                 liked = view_tag_interactions.liked + EXCLUDED.liked
            #         """, (view_id, tag, seconds, liked))
            #     conn.commit()
            i += 1
        else:
            print("Invalid input. Press 'n' or 'e'.")

# ---------------------
# Main CLI
# ---------------------

def main():
    conn = get_connection()
    try:
        username = input("Enter your username: ").strip()
        user_id = user_exists(conn, username)

        if not user_id:
            print("User not found. Creating new user...")
            user_id = create_user(conn, username)
            view_id, description = create_default_view(conn, user_id, ask_categories=True)
        else:
            # Existing user: fetch their default view
            view_id, description = get_default_view(conn, user_id)
            if not view_id:
                # Edge case: user exists but no default view
                view_id, description = create_default_view(conn, user_id, ask_categories=False)

        print(f"\nWelcome {username}! Showing your recommended posts from default view.")
        show_posts(conn, view_id, description)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
