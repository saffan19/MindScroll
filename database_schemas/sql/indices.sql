-- =========================
-- USERS INDICES
-- =========================
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- =========================
-- VIEWS INDICES
-- =========================
CREATE INDEX IF NOT EXISTS idx_views_user_id ON views(user_id);

-- =========================
-- VIEW CATEGORIES INDICES
-- =========================
CREATE INDEX IF NOT EXISTS idx_view_categories_view_id ON view_categories(view_id);
CREATE INDEX IF NOT EXISTS idx_view_categories_category ON view_categories(category);

-- =========================
-- ARTICLES INDICES
-- =========================
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published);
CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title);
CREATE INDEX IF NOT EXISTS idx_articles_content ON articles USING gin(to_tsvector('english', content));

-- =========================
-- RSS CATEGORIES INDICES
-- =========================
CREATE INDEX IF NOT EXISTS idx_rss_categories_article_guid ON rss_categories(article_guid);
CREATE INDEX IF NOT EXISTS idx_rss_categories_category ON rss_categories(category);

-- =========================
-- CATEGORIES INDICES
-- =========================
CREATE INDEX IF NOT EXISTS idx_categories_article_guid ON categories(article_guid);
CREATE INDEX IF NOT EXISTS idx_categories_category ON categories(category);

-- =========================
-- TAGS INDICES
-- =========================
CREATE INDEX IF NOT EXISTS idx_tags_article_guid ON tags(article_guid);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);

-- =========================
-- LLM CONTENT INDICES
-- =========================
CREATE INDEX IF NOT EXISTS idx_llm_content_article_guid ON llm_content(article_guid);

-- =========================
-- EMBEDDING VECTOR INDEX (for similarity search)
-- =========================
CREATE INDEX IF NOT EXISTS idx_articles_embedding ON articles USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
