import os

from google.adk.agents import Agent
from google.adk.models import Gemini


def get_weather(city: str) -> dict:
    """Returns the current weather report for a city.

    Args:
        city: Name of the city, e.g. "Paris".

    Returns:
        dict with "status" ("success" | "error") and "report" or "error_message".
    """
    # ponytail: hard-coded data; swap for a real weather API when you need real weather.
    reports = {
        "paris": "sunny, 24°C",
        "london": "rainy, 15°C",
        "tokyo": "cloudy, 21°C",
    }
    report = reports.get(city.strip().lower())
    if report is None:
        return {"status": "error", "error_message": f"No weather data for '{city}'."}
    return {"status": "success", "report": f"The weather in {city} is {report}."}


root_agent = Agent(
    name="weather_agent",
    # The model is called on the "global" endpoint so it works whatever region
    # Cloud Run runs in. Project comes from GOOGLE_CLOUD_PROJECT.
    model=Gemini(
        model=os.getenv("MODEL", "gemini-3.5-flash"),
        client_kwargs={"enterprise": True, "location": "global"},
    ),
    description="Answers questions about the current weather in a city.",
    instruction=(
        "You are a friendly weather assistant. "
        "When the user asks about the weather in a city, call get_weather. "
        "If the tool returns an error, say you have no data for that city."
    ),
    tools=[get_weather],
)
