import statistics as st
import requests

MARKET_URL = "https://raw.githubusercontent.com/exofri/ensim-trade-center/refs/heads/main/docs/data/market.json"

START_MONEY = 1000.0   # argent de depart
START_UNITS = 1000.0   # unites de depart (par produit)
RESERVE = 50.0         # reserve d'argent (comme le garde-fou du manuel)
SPLIT = 250            # les 250 premiers prix = "entrainement", le reste = "test"

# ---------- les trois regles ----------

def z_score(prices, n):
    window = prices[-n:]
    std = st.pstdev(window)
    if std == 0:
        return 0.0
    return (prices[-1] - st.mean(window)) / std

def clip(x):
    return max(-1.0, min(1.0, x))

def signal_cycle(prices, n=25, k=2.0):
    if len(prices) < n:
        return 0.0
    return clip(-z_score(prices, n) / k)

def signal_trend(prices, n=10, k2=0.2):
    if len(prices) <= n:
        return 0.0
    change = (prices[-1] - prices[-1 - n]) / prices[-1 - n]
    return clip(change / k2)

def signal_mix(prices):
    return clip(0.5 * signal_cycle(prices) + 0.5 * signal_trend(prices))

def signal_nothing(prices):
    return 0.0

STRATEGIES = {
    "ne rien faire": signal_nothing,
    "cycle": signal_cycle,
    "tendance": signal_trend,
    "melange": signal_mix,
}

# ---------- la simulation ----------

def simulate(prices, strategy, start, end):
    """Rejoue les pas start..end-1. A chaque pas, la regle ne voit que le passe."""
    money, units = START_MONEY, START_UNITS
    values = []
    n_trades = 0
    for t in range(start, end):
        history = prices[: t + 1]        # jamais le futur
        price = history[-1]
        sig = strategy(history)
        if sig > 0:
            wanted = 100 * sig
            affordable = max(0.0, (money - RESERVE) / price)
            bought = min(wanted, affordable)
            if bought > 0:
                money -= bought * price
                units += bought
                n_trades += 1
        elif sig < 0:
            sold = min(100 * -sig, units)
            if sold > 0:
                money += sold * price
                units -= sold
                n_trades += 1
        values.append(money + units * price)
    return values, n_trades

def max_drawdown(values):
    peak = values[0]
    worst = 0.0
    for v in values:
        peak = max(peak, v)
        worst = max(worst, (peak - v) / peak)
    return worst

def run_period(name, prices, start, end):
    base_values, _ = simulate(prices, signal_nothing, start, end)
    base_final = base_values[-1]
    print(f"  {'regle':<14}{'valeur finale':>14}{'gain vs rien':>14}{'pire chute':>12}{'transactions':>14}")
    for label, strat in STRATEGIES.items():
        values, n_trades = simulate(prices, strat, start, end)
        gain = values[-1] - base_final
        print(f"  {label:<14}{values[-1]:>14.1f}{gain:>14.1f}{max_drawdown(values)*100:>11.1f}%{n_trades:>14}")

def main(market):
    history = market["history"]
    n = len(history)
    print(f"{n} prix. Entrainement : pas 0-{SPLIT-1}. Test : pas {SPLIT}-{n-1}.")
    for p in market["products"]:
        prices = [row[p] for row in history]
        print(f"\n===== Produit {p} =====")
        print(" ENTRAINEMENT")
        run_period(p, prices, 0, SPLIT)
        print(" TEST")
        run_period(p, prices, SPLIT, n)

if __name__ == "__main__":
    market = requests.get(MARKET_URL, timeout=(10, 20)).json()
    main(market)