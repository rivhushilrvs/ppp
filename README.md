# 🤖 CryptoBot — AI Crypto Intelligence

Real-time crypto price tracker + news chatbot powered by Claude AI, LangGraph, and LangChain.

## Features
- 📊 Live prices for top 10 cryptocurrencies (CoinGecko API)
- 📰 Latest crypto news (CryptoPanic API)
- 🌍 Global market summary (market cap, BTC dominance)
- 🤖 Claude AI-powered chat with LangGraph tool-calling
- ⚡ Real-time ticker and live pulse sidebar

## Setup

### 1. Get your Anthropic API Key
Go to https://console.anthropic.com → API Keys → Create Key

### 2. Create .env file
```
cp .env.example .env
```
Then open `.env` and replace `your_anthropic_api_key_here` with your actual key.

### 3. Install & Run
See terminal commands below.

## Project Structure
```
crypto_chatbot/
├── app.py              ← Flask web server
├── agent.py            ← LangGraph agent with Claude
├── crypto_tools.py     ← LangChain tools (price, news, market)
├── requirements.txt
├── .env.example
├── .gitignore
└── templates/
    └── index.html      ← Full frontend UI
```
