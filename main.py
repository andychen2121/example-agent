from dotenv import load_dotenv
from agent import SierraAgent

load_dotenv()
agent = SierraAgent()

print("🌲 Welcome to the Sierra Assistant! Ask me anything. (Type 'exit' to quit)\n")

# Chat loop
while True:
    user_input = input("🧗 You: ")

    if user_input.strip().lower() in {"exit", "quit"}:
        print("🏕️ Sierra Agent: Until next time — stay wild out there!")
        break

    print("🏔️ Sierra Agent:", agent.handle(user_input))