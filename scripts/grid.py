import requests
from backtest import (MARKET_URL, SPLIT, simulate, max_drawdown,
                      signal_nothing, signal_cycle, signal_trend, clip)

def make_cycle(n, k, bias):
    def strat(prices):
        return clip(signal_cycle(prices, n=n, k=k) + bias)
    return strat

def make_trend(n, k2):
    def strat(prices):
        return signal_trend(prices, n=n, k2=k2)
    return strat

def build_candidates():
    cands = {"ne rien faire": signal_nothing}
    for n in (10, 25, 50, 75, 100):
        for k in (1, 2, 3):
            for b in (0.0, 0.1, 0.2):
                cands[f"cycle n={n} k={k} biais={b}"] = make_cycle(n, k, b)
    for n in (50, 75, 100):
        for k2 in (0.2, 0.5):
            cands[f"tendance n={n} k2={k2}"] = make_trend(n, k2)
    return cands

def evaluate(prices, strat, start, end):
    base, _ = simulate(prices, signal_nothing, start, end)
    vals, trades = simulate(prices, strat, start, end)
    return vals[-1] - base[-1], max_drawdown(vals), trades

def main(market):
    history = market["history"]
    n_all = len(history)
    cands = build_candidates()
    print(f"{n_all} prix. Regles testees : {len(cands)}. Classement fait sur l'ENTRAINEMENT (pas 0-{SPLIT-1}).")
    print("La colonne TEST ne sert qu'a verifier. On ne change rien apres l'avoir vue.")
    for p in market["products"]:
        prices = [row[p] for row in history]
        rows = []
        for name, strat in cands.items():
            g_tr, _, _ = evaluate(prices, strat, 0, SPLIT)
            g_te, dd_te, tr_te = evaluate(prices, strat, SPLIT, n_all)
            rows.append((name, g_tr, g_te, dd_te, tr_te))
        rows.sort(key=lambda r: r[1], reverse=True)
        print(f"\n===== Produit {p} : 8 meilleures regles sur l'entrainement =====")
        print(f"{'regle':<28}{'gain entrain.':>14}{'gain TEST':>12}{'chute test':>12}{'transac.':>10}")
        for r in rows[:8]:
            print(f"{r[0]:<28}{r[1]:>14.0f}{r[2]:>12.0f}{r[3]*100:>11.1f}%{r[4]:>10}")
        solid = [r for r in rows if r[1] > 0 and r[2] > 0]
        print(f"Regles positives dans les DEUX blocs : {len(solid)} sur {len(rows)}")
        nothing = [r for r in rows if r[0] == "ne rien faire"][0]
        print(f"Rappel 'ne rien faire' : chute test {nothing[3]*100:.1f}%")

if __name__ == "__main__":
    market = requests.get(MARKET_URL, timeout=(10, 20)).json()
    main(market)