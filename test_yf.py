import yfinance as yf

ticker = yf.Ticker("GOOGL")
info = ticker.info

print("recommendationKey:", info.get("recommendationKey"))
print("targetMeanPrice:", info.get("targetMeanPrice"))
print("currentPrice:", info.get("currentPrice"))

if info.get("targetMeanPrice") and info.get("currentPrice"):
    upside = ((info["targetMeanPrice"] - info["currentPrice"]) / info["currentPrice"]) * 100
    print("Implied Upside %:", round(upside, 2))
