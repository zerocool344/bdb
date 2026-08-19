import pandas as pd
url = "https://raw.githubusercontent.com/kovagent/congresskit/main/data/year=2026/congress-2026.parquet"
try:
    df = pd.read_parquet(url)
    pelosi = df[df['member_name'].str.contains('Pelosi', na=False, case=False)]
    
    def format_amount(row):
        try:
            low = float(row['amount_low']) if not pd.isna(row['amount_low']) else 0
            high = float(row['amount_high']) if not pd.isna(row['amount_high']) else 0
            
            def format_num(n):
                if n >= 1e6: return f"${int(n/1e6)}M"
                if n >= 1e3: return f"${int(n/1e3)}K"
                return f"${int(n)}"
                
            return f"{format_num(low)} - {format_num(high)}"
        except:
            return "Unknown"
            
    pelosi['Size'] = pelosi.apply(format_amount, axis=1)
    pelosi['Action'] = pelosi['txn_type'].str.replace('_', ' ').str.title()
    pelosi = pelosi.rename(columns={'ticker': 'Ticker', 'txn_date': 'Date Traded'})
    final = pelosi[['Ticker', 'Action', 'Date Traded', 'Size']].sort_values(by='Date Traded', ascending=False)
    print(final.head())
except Exception as e:
    print("Error:", e)
