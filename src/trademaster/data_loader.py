
# from src.trademaster.broker import AngelOneClient

# client = AngelOneClient()
# client._initialize_smart_api()  # If not already initialized
# tickers = client.fetch_all_nse_equity_symbols()
# ORB_TICKERS = tickers[:50]  # for example, top 50

# ORB_TICKERS = ["RELIANCE"]

ORB_TICKERS = [
    'POWERGRID',
    'SBIN',
    'ABFRL',
    'TATASTEEL',
    'HINDALCO',
    'UPL',
    'WIPRO',
    'NTPC',
    'COALINDIA',
]
# TODO write down different list of stocks based on the strategies they work on and use it from here
# eg : if one of the orb stock is not working as expected or a new stock need to be added it should be added here
YRB_TICKERS = [
    'POWERGRID',
    'SBIN',
    'TATASTEEL',
    'HINDALCO',
    'UPL',
    'WIPRO',
    'NTPC',
    'COALINDIA',
]
