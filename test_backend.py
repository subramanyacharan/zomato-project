import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parent / "phase6_backend" / "src"))

from main import app

client = TestClient(app)

def test_recommend():
    payload = {
        "location": "Bellandur",
        "budget": "high",
        "minimum_rating": 4.0,
        "top_n": 2,
        "mock": True
    }
    
    print("Sending request to /api/recommend...")
    response = client.post("/api/recommend", json=payload)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Number of recommendations: len({data['recommendations']})")
        for idx, rec in enumerate(data['recommendations']):
            print(f"{idx+1}. {rec['restaurant_name']} ({rec['rating']}*) - Reason: {rec['llm_reason']}")
        print("Test Passed!")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_recommend()
