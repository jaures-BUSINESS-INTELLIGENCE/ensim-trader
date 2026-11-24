import requests
import statistics as st

MARKET_URL = "https://raw.githubusercontent.com/exofri/ensim-trade-center/refs/heads/main/docs/data/market.json"

market = requests.get(MARKET_URL, timeout=(10, 20)).json()
history = market["history"]
print("Nombre de lignes :", len(history))

for p in market["products"]:
    prices = [row[p] for row in history]
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    print(f"\n=== Produit {p} ===")
    print("premier prix :", prices[0], "| dernier prix :", prices[-1])
    print("min :", min(prices), "| max :", max(prices), "| moyenne :", round(st.mean(prices), 3))
    print("ecart-type des variations (volatilite) :", round(st.pstdev(returns), 4))
    # ce que font les prix par blocs de 25 lignes
    print("prix tous les 25 pas :", [round(prices[i], 2) for i in range(0, len(prices), 25)])
    # apres une hausse, le prix a-t-il tendance a monter encore (+) ou a revenir (-) ?
    pairs = list(zip(returns[:-1], returns[1:]))
    mx, my = st.mean(r[0] for r in pairs), st.mean(r[1] for r in pairs)
    cov = sum((a - mx) * (b - my) for a, b in pairs) / len(pairs)
    corr = cov / (st.pstdev([r[0] for r in pairs]) * st.pstdev([r[1] for r in pairs]))
    print("correlation hausse -> hausse suivante :", round(corr, 3))
