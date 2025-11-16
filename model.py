# model.py
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")  # small & fast
# "all-MiniLM-L6-v2" is a small, fast model good for semantic similarity
clf = LogisticRegression(max_iter=200)

def fit_classifier(examples):  # examples: list[(text,label)]
    X = model.encode([t for t, _ in examples], normalize_embeddings=True)
    y = [lbl for _, lbl in examples]
    clf.fit(X, y)

def predict_label(text):
    v = model.encode([text], normalize_embeddings=True)
    proba = clf.predict_proba(v)[0]
    idx = proba.argmax()
    return clf.classes_[idx], float(proba[idx])
