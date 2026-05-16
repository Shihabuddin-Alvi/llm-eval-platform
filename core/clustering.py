from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

def cluster_failures(texts: list, n_clusters: int = 3) -> list:
    if len(texts) < n_clusters:
        n_clusters = len(texts)
    vectorizer = TfidfVectorizer()
    embeddings = vectorizer.fit_transform(texts).toarray()
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(embeddings)
    return [{"text": t, "cluster": int(l)} for t, l in zip(texts, labels)]