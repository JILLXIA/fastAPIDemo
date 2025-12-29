import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

# Import our tools
from tools.weather import get_weather_onecall
from tools.geocoding import geocode_city_tool
from tools.movie import discover_movies
from tools.places import get_places_osm
from tools.events import discover_events

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Load environment variables
load_dotenv()


def _build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a helpful weekend planner agent. "
            "You have access to tools:\n"
            "1. geocode_city_tool: resolves a city name into latitude and longitude.\n"
            "2. get_weather_onecall: fetches weather for a given location (latitude and longitude) or coordinates.\n"
            "3. discover_movies: discover movies based on different criteria like release date, genres, vote average, and popularity.\n"
            "4. get_places_osm: find places of interest (amenities) like restaurants, cafes, etc. using OpenStreetMap.\n"
            "5. discover_events: discover events (concerts, sports, etc.) using Ticketmaster based on location.\n"
            "Follow this plan to generate a response:\n"
            "1. Resolve the location using geocode_city_tool.\n"
            "2. Check the weather using get_weather_onecall and suggest appropriate clothing.\n"
            "3. Search for the latest popular movies using discover_movies.\n"
            "4. Find nearby cinemas using get_places_osm.\n"
            "5. Find restaurants based on user's cuisine preference using get_places_osm.\n"
            "6. Search for recent events based on user's interest using discover_events. Ensure you include the event URL in the response.\n"
            "Finally, combine all information into a complete weekend plan. "
            "IMPORTANT: Provide a single, comprehensive response. Do not ask the user for more information or follow-up questions. Make reasonable assumptions if needed to complete the plan.",
        ),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])


def _build_tools():
    return [
        geocode_city_tool,
        get_weather_onecall,
        discover_movies,
        get_places_osm,
        discover_events,
    ]


@lru_cache(maxsize=1)
def get_weekend_planner_executor(verbose: bool = False) -> AgentExecutor:
    """Build and cache the agent executor.

    Note: We keep this cached for performance (model + prompt + tool wiring).
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")

    model_name = os.getenv("OPENAI_MODEL", "gpt-5-nano")
    timeout_s = int(os.getenv("OPENAI_TIMEOUT_S", "30"))
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))

    tools = _build_tools()
    prompt = _build_prompt()

    model = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=None,
        timeout=timeout_s,
        api_key=openai_api_key,
    )

    agent = create_tool_calling_agent(model, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=verbose)


def run_weekend_planner(query: str, *, verbose: bool = False) -> dict:
    """Run the weekend planner agent for a given user query.

    Returns the raw LangChain invoke result (typically includes 'output').
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")

    executor = get_weekend_planner_executor(verbose=verbose)
    return executor.invoke({"input": query})


if __name__ == "__main__":
    # Tiny manual smoke run
    user_query = "Plan my new years holiday in San Jose"
    result = run_weekend_planner(user_query, verbose=True)
    print(result)
