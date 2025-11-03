import os
import json
from openai import OpenAI
import pytz
import uuid

from datetime import datetime
from collections import defaultdict

class SierraAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
        self.system_prompt = (
            "You are Sierra, an adventurous and cheerful outdoor gear expert. "
            "Use friendly, trail-inspired language, emojis like 🏕️🌲⛰️, and stay helpful and CONCISE. 3 sentence limit for all responses. "
            "If a question is unrelated to Sierra Outfitters, still answer politely but stay in character."
        )

        with open("data/CustomerOrders.json") as f:
            self.orders = json.load(f)
        with open("data/ProductCatalog.json") as f:
            self.products = json.load(f)

        # Running conversation history containing (user_input -> gpt_responses)
        self.history = []
        # Tag dictionary mapping (lowercase tag -> list of relevant products)
        self.tag_index = defaultdict(list)

        for product in self.products:
            for tag in product["Tags"]:
                normalized_tag = tag.lower()
                self.tag_index[normalized_tag].append(product)
    
    def handle(self, user_input: str) -> str:
        """
        Routes the user input to the correct functionality
        (order tracking, product recommendation, promo, or general GPT reply).
        """
        # Question type router
        intent_prompt = (
            "Classify the user's message into one or more of the following intent categories:\n\n"
            "- order: The user is asking about the status of a specific order they have already placed. "
            "This includes questions about tracking, shipping, delivery dates, or order numbers.\n"
            "- recommendation: The user is asking what to buy, looking for gear suggestions, or requesting "
            "something similar to a product or need (e.g. 'any good hiking backpacks?').\n"
            "- early_riser: The user is asking for a discount, promotional code, or any deal. "
            "This includes general questions about promotions or requests for discounts.\n"
            "- general: The message doesn’t fit the above — e.g. general conversation, brand questions, greetings, etc.\n\n"
            f"User message: '{user_input}'\n\n"
            "Respond with a comma-separated list of one or more intents from the list above. "
            "Use only the exact labels: order, recommendation, early_riser, general."
        )
        intent_response = self.call_gpt(intent_prompt)

        intents = [intent.strip() for intent in intent_response.split(",") if intent.strip()]

        responses = []
        if "order" in intents:
            responses.append(self.handle_order_info(user_input))
        if "recommendation" in intents:
            responses.append(self.handle_product_recommendation(user_input))
        if "early_riser" in intents:
            responses.append(self.handle_early_riser_promo())
        if not responses or "general" in intents:
            return self.call_gpt_and_update_history(user_input)
        
        additional_info = "\n".join(responses)
        compiled_prompt = (
            f"User question: {user_input}. "
            f"Use the following information to best answer the user's question: {additional_info}"
        )
        
        return self.call_gpt_and_update_history(compiled_prompt)

    def handle_order_info(self, query) -> str:
        """
        Prompts the user for their email + order number,
        finds the matching order info, and uses GPT to return a natural reply.
        """
        email = input("Please provide your email: ")
        order_number = input("Please provide your order number: ")

        match = next(
            (o for o in self.orders if o["Email"] == email and o["OrderNumber"] == order_number),
            None
        )

        if match:
            status = match["Status"]
            tracking = match["TrackingNumber"]
            base = (
                f"Order {order_number} is {status}. "
                f"Tracking link: https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking}"
            )
        else:
            base = "Couldn't find an order with that email and order number."

        return base

    def handle_product_recommendation(self, query: str) -> str:
        """
        Matches user query to product tags or names dynamically using GPT.
        """
        tag_list = sorted(self.tag_index.keys())
        tag_csv = ", ".join(tag_list)

        # dynamically generate most relevant tags from existing tag set
        tag_selection_prompt = (
            f"You are an assistant helping customers find gear.\n"
            f"Available product tags are: {tag_csv}.\n"
            f"User said: '{query}'\n"
            f"Choose up to 8 relevant tags from the list based on the user's request."
            f"Respond with only the chosen tags, as a comma-separated list."
        )
        tag_response = self.call_gpt(tag_selection_prompt)

        extracted_tags = [tag.strip() for tag in tag_response.split(",")]
        valid_tags = [tag for tag in extracted_tags if tag in self.tag_index]

        # gather set of possible recommendations
        matched_products = []
        for tag in valid_tags:
            matched_products.extend(self.tag_index[tag])

        fallback = (
            "Product Status: Couldn't find anything that matches. Ask the user to describe what they're looking for in a bit more detail."
        )
        if not matched_products:
            return fallback

        # narrow set down to a single option 
        summary_text = "\n".join(f"{p['ProductName']} — {p['Description']}" for p in matched_products)
        product_selection_prompt = (
            f"You are an assistant helping customers find gear.\n"
            f"User said: '{query}'\n"
            f"Available products: {summary_text}"
            f"Choose ONE of the products that best matches the user's request.\n"
            f"Response format:"
            f"Recommended Purchase for Customer: Product Name - Product Description\n"
            f"If nothing relevant is available, return the following text: {fallback}"
        )
        product_selection_response = self.call_gpt(product_selection_prompt)
        
        return product_selection_response


    def handle_early_riser_promo(self) -> str:
        """
        Checks current time (Pacific Time). If within 8–10 AM, generates a discount code.
        """
        now = datetime.now(pytz.timezone("US/Pacific"))
        if 8 <= now.hour < 10:
            code = "SIERRA-" + str(uuid.uuid4())[:4].upper()
            base = f"This user qualifies for the Early Riser promotion! They may use discount code {code} for 10% off."
        else:
            base = "The Early Riser promotion only runs from 8–10 AM Pacific Time. This user does not currently qualify."

        return base

    def call_gpt(self, prompt: str, temperature: float = 0) -> str:
        try:
            return self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            ).choices[0].message.content.strip()
        except Exception as e:
            print(f"[GPT error] {e}")
            return "Oops! Looks like I'm having trouble reaching the trailhead 🥾. Try again in a moment?"

    def call_gpt_and_update_history(self, new_user_message: str) -> str:
        """
        Sends conversation to GPT:
        - Includes system prompt
        - Includes user/assistant history
        - Adds new_user_message as the latest user content
        """
        messages = [{"role": "system", "content": self.system_prompt}] + \
                   self.history + \
                   [{"role": "user", "content": new_user_message}]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[GPT error] {e}")
            return "Something went off trail 🌲— please try again shortly!"

        # Save actual conversation turns
        self.history.append({"role": "user", "content": new_user_message})
        self.history.append({"role": "assistant", "content": reply})

        return reply
