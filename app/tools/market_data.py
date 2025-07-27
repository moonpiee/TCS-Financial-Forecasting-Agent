import requests
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)

def fetch_market_data():
    url = "https://www.screener.in/company/TCS/#quarters"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Network error while fetching market data: {e}")
        return {}

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        ratios = {}
        ratios_ul = soup.find("ul", id="top-ratios")
        if ratios_ul:
            for li in ratios_ul.find_all("li", class_="flex flex-space-between"):
                label_span = li.find("span", class_="name")
                value_span = li.find("span", class_="nowrap")
                if label_span and value_span:
                    label = label_span.text.strip()
                    value = value_span.text.strip()
                    ratios[label] = value

        desired_keys = [
            "Market Cap",
            "Current Price",
            "High / Low",
            "Stock P/E",
            "Book Value",
            "Dividend Yield",
            "ROCE",
            "ROE",
            "Face Value"
        ]

        filtered = {}
        for key, val in ratios.items():
            if key in desired_keys:
                cleaned = val.replace("\n", " ")
                cleaned = re.sub(r"\s+", " ", cleaned)
                cleaned = re.sub(r"\s+(Cr\.|%|₹)", r" \1", cleaned)
                cleaned = cleaned.strip()
                filtered[key] = cleaned
        return filtered
    except Exception as e:
        logger.error(f"Error parsing market data: {e}")
        return {}