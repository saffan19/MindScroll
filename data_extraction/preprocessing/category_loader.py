def load_categories(filename="resources/categories.txt"):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]