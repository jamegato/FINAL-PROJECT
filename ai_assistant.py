import os
from typing import List, Optional, Tuple
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from models import InventoryManager, SalesManager, FlagManager

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found. AI Assistant will use fallback responses.")
    st.stop()
class AIAssistant:
    """AI Assistant that provides contextual help about inventory management."""


    def __init__(
        self,
        inventory_manager: InventoryManager,
        sales_manager: SalesManager,
        flag_manager: FlagManager,
        use_openai: bool = True
    ):
        """
        Initialize the AI Assistant.
        
        Args:
            inventory_manager: Reference to inventory for context
            sales_manager: Reference to sales data for context
            flag_manager: Reference to flags for context
            use_openai: Whether to use OpenAI (True) or fallback responses (False)
        """
        self.inventory = inventory_manager
        self.sales = sales_manager
        self.flags = flag_manager
        self.use_openai = use_openai and OPENAI_AVAILABLE
        self.client = None

        if self.use_openai:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                self.use_openai = False

    def get_context_summary(self) -> str:
        """Build a summary of current inventory state for context."""
        active_count = len(self.inventory.get_active_products())
        low_stock = len(self.inventory.get_low_stock_items(strict=True))
        total_revenue = self.sales.get_total_revenue()
        open_flags = self.flags.get_open_flag_count()

        return f"""
Current Business State:
- Active Products: {active_count}
- Low Stock Items: {low_stock}
- Total Revenue: ${total_revenue:.2f}
- Open Low-Stock Flags: {open_flags}
"""

    def generate_response(self, user_message: str) -> str:
        """
        Generate an AI response to a user query.
        
        Args:
            user_message: The user's question or prompt
            
        Returns:
            The assistant's response
        """
        if self.use_openai and self.client:
            return self._generate_openai_response(user_message)
        else:
            return self._generate_fallback_response(user_message)

    def _generate_openai_response(self, user_message: str) -> str:
        """Generate response using OpenAI API."""
        try:
            system_prompt = f"""You are a helpful AI assistant for a small business inventory management system. 
You have access to the following business information:

{self.get_context_summary()}

You help users with:
- Inventory management and stock levels
- Sales tracking and revenue analysis
- Low-stock alerts and inventory risks
- Best practices for inventory control

Be concise, practical, and focused on actionable advice for inventory management.
Keep responses under 150 words."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=300,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return self._generate_fallback_response(user_message)

    def _generate_fallback_response(self, user_message: str) -> str:
        """Generate a fallback response using pattern matching."""
        prompt = user_message.lower().strip()

        # Greeting
        if any(word in prompt for word in ["hello", "hi", "hey", "greetings"]):
            return "Hello! I'm your inventory assistant. I can help you with stock levels, sales analysis, and low-stock alerts. What would you like to know?"

        # Low stock inquiries
        if "low" in prompt and "stock" in prompt:
            low_items = self.inventory.get_low_stock_items(strict=True)
            if not low_items:
                return "✓ Great news! No items are currently below their low-stock threshold. Your inventory is well-stocked."
            items_list = "\n".join([f"- {item.name} (Stock: {item.stock}, Threshold: {item.low_stock_threshold})" for item in low_items])
            return f"⚠️ The following items are below low-stock threshold:\n{items_list}"

        # Revenue inquiries
        if "revenue" in prompt or "sales" in prompt or "income" in prompt:
            revenue = self.sales.get_total_revenue()
            count = self.sales.get_sales_count()
            avg = self.sales.get_average_sale_value()
            return f"Sales Summary:\n- Total Sales: {count}\n- Total Revenue: ${revenue:.2f}\n- Average Sale: ${avg:.2f}"

        # Flag/Alert inquiries
        if "flag" in prompt or "alert" in prompt or "risk" in prompt:
            open_flags = self.flags.get_open_flags()
            if not open_flags:
                return "✓ No open alerts. All flagged items have been acknowledged."
            flags_list = "\n".join([f"- {flag.product_name}: {flag.note}" for flag in open_flags[:5]])
            return f"Open Alerts ({len(open_flags)} total):\n{flags_list}"

        # Product count
        if "product" in prompt or "inventory" in prompt or "catalog" in prompt:
            active = len(self.inventory.get_active_products())
            total = len(self.inventory.products)
            discontinued = total - active
            return f"Inventory Status:\n- Active Products: {active}\n- Discontinued: {discontinued}\n- Total Value: ${self.inventory.calculate_total_value():.2f}"

        # Help request
        if "help" in prompt or "what can you" in prompt:
            return """I can help with:
• Low stock alerts - Ask about items below threshold
• Sales & revenue - Get sales performance data
• Inventory overview - Check total products and value
• Guidance - Ask how to use any feature

What would you like to know?"""

        # Default response
        return "I can help with inventory management questions. Ask me about low stock items, sales performance, open alerts, or product inventory."

    def get_welcome_message(self) -> str:
        """Get the initial greeting message."""
        return "👋 Hello! I'm your inventory management AI assistant. I can help you with low-stock alerts, sales analysis, inventory insights, and operational guidance. Feel free to ask me anything about your inventory!"
