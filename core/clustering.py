from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def cluster_failures(texts: list, n_clusters: int = 3) -> list:
    if len(texts) < n_clusters:
        n_clusters = len(texts)
    embeddings = model.encode(texts)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(embeddings)
    return [{"text": t, "cluster": int(l)} for t, l in zip(texts, labels)]