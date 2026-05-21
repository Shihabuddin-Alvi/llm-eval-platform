import os
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "https://criterion-api-c7mf.onrender.com")
API_KEY = os.getenv("CRITERION_API_KEY", "")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

mcp = FastMCP("Criterion")

@mcp.tool()
def run_eval(input: str, prediction: str, reference: str, grader_name: str = "exact_match") -> dict:
    """Run a single evaluation job."""
    payload = {
        "input": input,
        "prediction": prediction,
        "reference": reference,
        "grader_name": grader_name,
        "model_name": "mcp-agent"
    }
    r = httpx.post(f"{API_URL}/jobs", json=payload, headers=HEADERS, timeout=30)
    return r.json()

@mcp.tool()
def get_leaderboard() -> list:
    """Get the model leaderboard ranked by average score."""
    r = httpx.get(f"{API_URL}/jobs/leaderboard", headers=HEADERS, timeout=30)
    return r.json()

@mcp.tool()
def get_clusters(texts: list, n_clusters: int = 3) -> list:
    """Cluster a list of failure texts into groups using TF-IDF and KMeans."""
    r = httpx.post(
        f"{API_URL}/jobs/failures/cluster",
        json=texts,
        headers=HEADERS,
        params={"n_clusters": n_clusters},
        timeout=30
    )
    return r.json()

if __name__ == "__main__":
    mcp.run()