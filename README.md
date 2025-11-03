# Sierra Assistant
A cheerful, trail-savvy AI chatbot for Sierra Outfitters that answers order questions, suggests outdoor gear, and offers time-sensitive promotions — all in a fun, nature-loving tone!

# Features
- Order Tracking: Ask about your order — it’ll prompt you for your email + order number, then return live tracking info.
- Gear Recommendations: Describe what you're looking for (e.g., "best backpack for snow hikes"), and it’ll match relevant products from the catalog.
- Early Riser Promo: Check for a 10% off discount — available daily between 8–10 AM Pacific Time.

# How to Run
1. Clone & Install
```
git clone https://github.com/yourname/sierra-assistant.git
cd sierra-assistant
pip install -r requirements.txt
```
2. Setup OpenAI API Key
Create a `.env` file
```
OPENAI_API_KEY=your-openai-key
```
3. Run Chat Agent
```
python main.py
```