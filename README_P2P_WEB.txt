P2P Merchant Web Control

How to run (in this environment):
1) Install deps
   python3 -m pip install --user -r /workspace/requirements.txt

2) Start web app (do not close this terminal)
   python3 -m p2p_merchant_web

3) Open in browser
   http://localhost:8000/

Mock vs Binance mode:
- By default, runs in MOCK mode (no calls to Binance). You can create/edit/pause ads locally.
- To enable Binance Merchant mode (requires approved merchant API keys):
  export BINANCE_API_KEY=your_key
  export BINANCE_API_SECRET=your_secret
  python3 -m p2p_merchant_web

Notes:
- "Push" button attempts to push updates via provider. In MOCK mode it is a no-op.
- Real Binance Merchant API integration requires endpoints and permissions; wire up in p2p_merchant_web/provider.py
- For geo-restricted regions, run the app on a VPS in an allowed region.
