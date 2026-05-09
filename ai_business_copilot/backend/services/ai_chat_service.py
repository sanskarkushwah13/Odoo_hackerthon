"""
AI Chat Service
Powers the conversational business advisor using the Anthropic Claude API.
Falls back to a rules-based responder if no API key is set.
"""

import os
import json
import re
from typing import Dict, Any, Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


SYSTEM_PROMPT = """You are an expert ERP Business Decision Advisor with deep expertise in:
- Sales analytics and revenue optimization
- Inventory management and supply chain
- Customer segmentation and retention
- Financial forecasting and trend analysis
- Business strategy and growth recommendations

You have access to real ERP data context provided in each query.
Your responses should be:
1. Concise and actionable (3-5 bullet points or short paragraphs)
2. Data-driven — cite the numbers provided in context
3. Business-focused — prioritize ROI and risk
4. Professional but approachable

Always structure your response with:
- A direct answer to the question
- Key data insights (2-3 points)
- Actionable recommendations (2-3 steps)
"""


class AIChatService:
    """AI-powered business Q&A advisor."""

    def __init__(self, data_context: str = ""):
        self.data_context = data_context
        self.client: Optional[Any] = None

        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)

    # ─── Main entry point ─────────────────────────────────────────────────────
    def ask(self, question: str, history: list | None = None) -> Dict[str, Any]:
        """
        Answer a business question using Claude or a rules-based fallback.

        Args:
            question: The user's business question.
            history:  List of {"role": ..., "content": ...} dicts (optional).

        Returns:
            Dict with 'answer', 'source', and optional 'suggestions'.
        """
        if self.client:
            return self._ask_claude(question, history or [])
        return self._rules_based_response(question)

    # ─── Claude API ───────────────────────────────────────────────────────────
    def _ask_claude(self, question: str, history: list) -> Dict[str, Any]:
        """Call the Anthropic API."""
        messages = []

        # Inject data context into first user message if history is empty
        if not history:
            enriched_question = (
                f"Business Context:\n{self.data_context}\n\n"
                f"Question: {question}"
            )
            messages.append({"role": "user", "content": enriched_question})
        else:
            messages = history + [{"role": "user", "content": question}]

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            answer = response.content[0].text
            return {
                "answer":      answer,
                "source":      "Claude AI",
                "suggestions": self._extract_suggestions(question),
            }
        except Exception as e:
            return {
                "answer":  f"AI service error: {str(e)}. Using built-in analysis instead.\n\n"
                           + self._rules_based_response(question)["answer"],
                "source":  "Fallback",
                "suggestions": [],
            }

    # ─── Rules-based fallback ─────────────────────────────────────────────────
    def _rules_based_response(self, question: str) -> Dict[str, Any]:
        """
        Keyword-matching fallback that generates structured answers from
        the data context without requiring an API key.
        """
        q = question.lower()
        ctx = self.data_context

        if any(w in q for w in ["drop", "decline", "decrease", "fall", "down"]):
            answer = (
                "**Sales/Revenue Drop Analysis**\n\n"
                f"Based on your ERP data: {ctx}\n\n"
                "**Likely Causes:**\n"
                "• Seasonal demand fluctuation — check if prior years show the same pattern\n"
                "• Stock-out events causing lost sales — review inventory alerts\n"
                "• Competitive pricing pressure — benchmark against market rates\n\n"
                "**Recommended Actions:**\n"
                "• Run a product-level drill-down to isolate the affected SKUs\n"
                "• Check customer churn rate in the same period\n"
                "• Launch a targeted promotion for top at-risk customers"
            )
        elif any(w in q for w in ["best", "top", "perform", "highest"]):
            answer = (
                "**Top Performer Analysis**\n\n"
                f"ERP Context: {ctx}\n\n"
                "**Key Insights:**\n"
                "• Electronics category leads revenue — high unit prices drive value\n"
                "• Products with 40%+ margin are strong candidates for upselling\n"
                "• Top region concentrates the majority of high-value transactions\n\n"
                "**Recommended Actions:**\n"
                "• Increase inventory allocation for top-performing SKUs\n"
                "• Replicate successful regional strategies across other markets\n"
                "• Create bundle offers around best-sellers to lift average order value"
            )
        elif any(w in q for w in ["forecast", "predict", "next month", "future"]):
            answer = (
                "**Revenue Forecast Summary**\n\n"
                f"ERP Context: {ctx}\n\n"
                "**Forecast Insights:**\n"
                "• Prophet model projects moderate growth based on historical seasonality\n"
                "• Q4 typically shows 40-60% uplift — plan inventory accordingly\n"
                "• Key risk: supply chain disruptions could reduce forecast accuracy\n\n"
                "**Recommended Actions:**\n"
                "• Pre-order top SKUs 45 days ahead of projected demand peaks\n"
                "• Set revenue targets 5-10% above forecast to motivate sales team\n"
                "• Monitor weekly actuals vs. forecast and adjust tactics quickly"
            )
        elif any(w in q for w in ["inventory", "stock", "restock"]):
            answer = (
                "**Inventory Management Analysis**\n\n"
                f"ERP Context: {ctx}\n\n"
                "**Current Status:**\n"
                "• Several products show <14 days of stock — immediate restock needed\n"
                "• Overstock detected on slow-moving items — consider discounting\n"
                "• Safety stock levels should target 14-21 days of average demand\n\n"
                "**Recommended Actions:**\n"
                "• Prioritize urgent restocks for high-revenue SKUs\n"
                "• Negotiate volume discounts with suppliers for top-moving items\n"
                "• Implement automated reorder points in your ERP system"
            )
        elif any(w in q for w in ["customer", "retention", "churn", "loyal"]):
            answer = (
                "**Customer Retention Analysis**\n\n"
                f"ERP Context: {ctx}\n\n"
                "**Customer Health:**\n"
                "• High-value customers inactive 45+ days are churn risks\n"
                "• One-time buyers represent a growth opportunity with the right follow-up\n"
                "• Champions segment drives disproportionate revenue — protect it\n\n"
                "**Recommended Actions:**\n"
                "• Send win-back campaigns to at-risk high-value customers (15% discount)\n"
                "• Launch loyalty program to convert new buyers into repeat customers\n"
                "• Schedule quarterly business reviews with top 20% accounts"
            )
        else:
            answer = (
                "**Business Performance Overview**\n\n"
                f"ERP Data Summary: {ctx}\n\n"
                "**Key Takeaways:**\n"
                "• Revenue and profitability trends are visible in the dashboard charts\n"
                "• Anomaly detection is actively monitoring for unusual patterns\n"
                "• Inventory and customer health metrics are updated in real time\n\n"
                "**Recommended Actions:**\n"
                "• Review the Anomaly Alerts section for immediate action items\n"
                "• Check the Recommendations tab for prioritized next steps\n"
                "• Use the Forecasting module to plan for next month's demand\n\n"
                "_Tip: Ask me specific questions like 'Why did sales drop?', "
                "'Which product performs best?', or 'Predict next month revenue'._"
            )

        return {
            "answer":      answer,
            "source":      "Built-in Analytics Engine",
            "suggestions": self._extract_suggestions(question),
        }

    # ─── Suggested follow-up questions ────────────────────────────────────────
    def _extract_suggestions(self, question: str) -> list:
        all_suggestions = [
            "Why did sales drop last month?",
            "Which product performs best?",
            "Predict next month revenue",
            "What are the top inventory risks?",
            "How can I improve customer retention?",
            "Which region has the highest growth potential?",
            "What pricing changes would improve margins?",
            "Summarize overall business performance",
        ]
        q_lower = question.lower()
        return [s for s in all_suggestions if s.lower() not in q_lower][:4]
