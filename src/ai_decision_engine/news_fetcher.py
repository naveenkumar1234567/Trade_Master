import requests
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def get_latest_news(company_name: str) -> str:
    """Fetch the latest news headline for a given company using NewsAPI."""
    if not NEWS_API_KEY:
        raise ValueError("Missing NEWS_API_KEY in .env file")

    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={company_name}&"
        f"sortBy=publishedAt&"
        f"language=en&"
        f"apiKey={NEWS_API_KEY}"
    )

    try:
        response = requests.get(url)
        data = response.json()

        if data["status"] != "ok" or not data["articles"]:
            return f"No recent news found for {company_name}."

        # Return the title of the most recent article
        return data["articles"][0]["title"]

    except Exception as e:
        print(f"[ERROR] Failed to fetch news for {company_name}: {e}")
        return f"No news available for {company_name}."
