from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def classify_content(text, categories):
    result = classifier(text, candidate_labels=categories, multi_label=True)
    top5 = sorted(zip(result["labels"], result["scores"]), key=lambda x: x[1], reverse=True)[:5]
    return [{"category": label, "score": float(score)} for label, score in top5]