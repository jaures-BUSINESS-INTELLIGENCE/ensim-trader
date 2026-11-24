import json, time
import requests

MARKET_URL = "https://raw.githubusercontent.com/exofri/ensim-trade-center/refs/heads/main/docs/data/market.json"
HOLDINGS_URL = "https://raw.githubusercontent.com/exofri/ensim-trade-center/refs/heads/main/traders/franck/holdings.json"

MIN_MONEY_RESERVE = 50  # on ne dépense jamais sous cette réserve

def fetch_json(url):
    resp = requests.get(url, timeout=(10, 20))
    resp.raise_for_status()
    return resp.json()

def compute_signal(prices):
    # À implémenter par toi. Pour l'instant : ne rien faire (0.0).
    return 0.0

def apply_budget_guard(raw_signal, money, price, reserve=MIN_MONEY_RESERVE):
    if raw_signal <= 0:
        return raw_signal
    if money <= reserve:
        return 0.0
    max_affordable_units = (money - reserve) / price
    desired_units = 100 * raw_signal
    if desired_units <= max_affordable_units:
        return raw_signal
    return round(max_affordable_units / 100, 3)

def main():
    market = fetch_json(MARKET_URL)
    holdings = fetch_json(HOLDINGS_URL)
    products = market["products"]
    history = market["history"]

    decision = {}
    for p in products:
        prices = [row[p] for row in history]
        raw = compute_signal(prices)
        current_price = prices[-1] if prices else 0
        decision[p] = round(apply_budget_guard(raw, holdings["money"], current_price), 3)

    decision["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open("decision.json", "w") as f:
        json.dump(decision, f, indent=2)
    print(f"Wrote decision.json: {decision}")

if __name__ == "__main__":
    main()
