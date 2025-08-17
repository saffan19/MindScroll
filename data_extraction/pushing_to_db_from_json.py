import json
import psycopg2
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer

# -------------------------------
# DB connection
# -------------------------------
conn = psycopg2.connect(
    dbname="mindscroll",
    user="postgres",
    password="asdfghjkl",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# -------------------------------
# Load embedding model
# -------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384-dim (fast)

# -------------------------------
# Load JSON data
# -------------------------------
with open("content/content.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for article in data:
    guid = article.get("guid")
    title = article.get("title")
    link = article.get("link")
    published = article.get("published")
    summary = article.get("summary")
    description = article.get("description")
    image_url = article.get("image_url")
    author = article.get("author")
    source = article.get("source")
    content_text = article.get("content")

    # Create embedding (title + content)
    text_for_embedding = (title + " " + content_text)[:2000]
    embedding = model.encode(text_for_embedding).tolist()

    # -------------------------------
    # Insert into articles table
    # -------------------------------
    cur.execute("""
        INSERT INTO articles
        (guid, title, link, published, summary, description, image_url, author, source, content, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (guid) DO NOTHING;
    """, (
        guid, title, link, published, summary, description, image_url, author, source, content_text, embedding
    ))

    # -------------------------------
    # Insert RSS categories
    # -------------------------------
    rss_categories = article.get("rss_categories", [])
    if rss_categories:
        values = [(guid, cat) for cat in rss_categories]
        execute_values(cur,
            "INSERT INTO rss_categories (article_guid, category) VALUES %s ON CONFLICT DO NOTHING",
            values
        )

    # -------------------------------
    # Insert categories with score
    # -------------------------------
    categories = article.get("categories", [])
    if categories:
        values = [(guid, cat.get("category"), cat.get("score")) for cat in categories]
        execute_values(cur,
            "INSERT INTO categories (article_guid, category, score) VALUES %s ON CONFLICT DO NOTHING",
            values
        )

    # -------------------------------
    # Insert LLM content
    # -------------------------------
    llm_content = article.get("LLM_CONTENT")
    if llm_content:
        cur.execute("""
            INSERT INTO llm_content (article_guid, title, content)
            VALUES (%s, %s, %s)
            ON CONFLICT (article_guid) DO NOTHING;
        """, (guid, llm_content.get("title"), llm_content.get("content")))

# -------------------------------
# Commit and close
# -------------------------------
conn.commit()
cur.close()
conn.close()

print("All articles inserted successfully!")
