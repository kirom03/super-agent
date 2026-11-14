# Crypto Watcher Skill

When the user asks for crypto prices (BTC, ETH, SOL), token analytics, or address balances:
1. Use `call_rest_api` or `search_web` to retrieve current market rates from free public APIs (e.g. CoinGecko, Binance public ticker).
2. For wallet balances, use public EVM RPC endpoints in read-only mode (`eth_getBalance`).
3. Never ask for or store private keys or seed phrases.
