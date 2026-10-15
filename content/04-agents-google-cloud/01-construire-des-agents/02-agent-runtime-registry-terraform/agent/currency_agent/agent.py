import os

from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent
from google.adk.models import Gemini

# ponytail: fixed demo rates; replace with a real FX API when you need live rates.
RATES_TO_EUR = {"EUR": 1.0, "USD": 0.86, "GBP": 1.17, "JPY": 0.0058, "MAD": 0.092}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Converts an amount of money from one currency to another.

    Args:
        amount: The amount to convert, e.g. 100.
        from_currency: ISO code of the source currency, e.g. "USD".
        to_currency: ISO code of the target currency, e.g. "EUR".

    Returns:
        dict with "status" and either "result" or "error_message".
    """
    src, dst = from_currency.upper(), to_currency.upper()
    unknown = [c for c in (src, dst) if c not in RATES_TO_EUR]
    if unknown:
        return {
            "status": "error",
            "error_message": f"Unsupported currency: {', '.join(unknown)}. Supported: {', '.join(RATES_TO_EUR)}.",
        }
    value = amount * RATES_TO_EUR[src] / RATES_TO_EUR[dst]
    return {"status": "success", "result": f"{amount:g} {src} = {value:.2f} {dst}"}


root_agent = Agent(
    name="currency_agent",
    model=Gemini(
        model=os.getenv("MODEL", "gemini-3.5-flash"),
        client_kwargs={"enterprise": True, "location": "global"},
    ),
    description="Converts amounts between currencies (EUR, USD, GBP, JPY, MAD).",
    instruction=(
        "You are a currency assistant. For any conversion question call convert_currency. "
        "Answer in one short sentence with the converted amount. "
        "If the tool returns an error, explain which currencies are supported."
    ),
    tools=[convert_currency],
)

# Agent Runtime imports this object (entrypoint_object = "app").
# AdkApp wraps the agent and exposes create_session / stream_query / ... as API methods,
# with managed sessions and memory provided by Agent Runtime.
app = AdkApp(agent=root_agent)


if __name__ == "__main__":
    assert convert_currency(100, "eur", "eur")["result"] == "100 EUR = 100.00 EUR"
    assert convert_currency(100, "USD", "EUR")["result"] == "100 USD = 86.00 EUR"
    assert convert_currency(1, "XYZ", "EUR")["status"] == "error"
    print("convert_currency OK")
