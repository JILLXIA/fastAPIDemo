import os
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def create_weekend_planner_agent():
    """
    Create a weekend planner agent that automatically chains:
    1. geocode_city_tool → get coordinates
    2. get_weather_onecall → fetch weather & clothing suggestions
    3. discover_movies -> discover popular movies
    4. get_places_osm -> find cinemas and restaurants
    5. discover_events -> find events
    """

    # Tools in the agent
    tools = [
        geocode_city_tool,
        get_weather_onecall,
        discover_movies,
        get_places_osm,
        discover_events
    ]

    # LLM model
    model = ChatOpenAI(
        model="gpt-5-nano",
        temperature=0.1,
        max_tokens=None,
        timeout=30,
        api_key=OPENAI_API_KEY
    )

    # Prompt template: guide the agent to chain tools
    prompt = ChatPromptTemplate.from_messages([
        ("system",
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
         "IMPORTANT: Provide a single, comprehensive response. Do not ask the user for more information or follow-up questions. Make reasonable assumptions if needed to complete the plan."),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad")
    ])

    # Create agent
    agent = create_tool_calling_agent(model, tools=tools, prompt=prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Example query: the agent automatically chains geocode → weather
    user_query = "Plan my new years holiday in San Jose"
    result = executor.invoke({"input": user_query})

    print(result)


if __name__ == "__main__":
    create_weekend_planner_agent()
