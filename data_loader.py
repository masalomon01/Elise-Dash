import pandas as pd

def load_data():
    df = pd.read_csv("data.csv")
    df["Base Annual Contract Value"] = df["Base Annual Contract Value"].replace('[\$,]', '', regex=True).astype(float)
    df["Created Date"] = pd.to_datetime(df["Created Date"], errors="coerce")
    df["Close Date"] = pd.to_datetime(df["Close Date"], errors="coerce")
    df["Created Quarter"] = df["Created Date"].dt.to_period("Q")
    df["Close Quarter"] = df["Close Date"].dt.to_period("Q")
    df["Is_Won"] = df["Current Stage (as of data pull)"] == "Closed Won"
    df["Is_Lost"] = df["Current Stage (as of data pull)"] == "Closed Lost"
    df["Deal Velocity (Days)"] = df.apply(lambda x: (x["Close Date"] - x["Created Date"]).days if x["Is_Won"] else None, axis=1)
    bins = [0, 10000, 50000, 100000, 500000, float('inf')]
    labels = ["<10K", "10-50K", "50-100K", "100-500K", "500K+"]
    df["Deal Size Band"] = pd.cut(df["Base Annual Contract Value"], bins=bins, labels=labels)
    return df
