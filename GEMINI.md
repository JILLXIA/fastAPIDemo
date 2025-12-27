# GEMINI.md - Weekend Planner Agent

This document outlines the plan for building a Weekend Planner Agent.

## 1. Project Goal

The goal is to create an AI agent that helps users plan their weekend activities. The agent will take user preferences as input and generate a personalized weekend itinerary.

## 2. Features

- **User Preference Input:** Allow users to specify their location, interests, budget, and companions.
- **Activity Suggestions:** Suggest activities, restaurants, and events based on user preferences.
- **Itinerary Generation:** Create a structured weekend plan with a schedule.
- **External Tool Integration:** Use external APIs to gather real-time information about places, weather, and events.

## 3. Proposed Tech Stack

- **Language:** Python
- **Core LLM:** Gemini
- **Framework:** FastAPI (for a potential web API)
- **External APIs:**
    - Google Places API (for location-based suggestions)
    - OpenWeatherMap API (for weather forecasts)
    - A suitable event API (e.g., Ticketmaster, Eventbrite)

## 4. Development Plan

### Phase 1: Core Agent & Project Setup

- **Task 1.1: Project Scaffolding:** Set up a new Python project with a virtual environment. Create `main.py`, `requirements.txt`, and a `tools` directory.
- **Task 1.2: Basic Agent Logic:** Implement a basic agent loop in `main.py`. This will take a hardcoded user prompt and use the Gemini LLM to generate a simple weekend plan.
- **Task 1.3: User Input:** Implement a way to get user input, either through the command line or a simple web form.

### Phase 2: Tool Integration

- **Task 2.1: Weather Tool:** Create a tool that uses the OpenWeatherMap API to get the weather forecast for a given location and date.
- **Task 2.2: Places Tool:** Create a tool that uses the Google Places API to find restaurants, attractions, etc., based on user interests and location.
- **Task 2.3: Events Tool:** Create a tool to find local events.
- **Task 2.4: Integrate Tools with Agent:** Modify the agent to be able to use these tools to gather information and generate a more informed plan. The LLM will decide which tool to use.

### Phase 3: Itinerary Generation & Output

- **Task 3.1: Structured Output:** Define a Pydantic model for a structured itinerary (e.g., with Day, Time, Activity, Location).
- **Task 3.2: Output Formatting:** Instruct the LLM to generate the plan in the defined structured format.
- **Task 3.3: User-Friendly Display:** Display the generated itinerary to the user in a clean and readable format.

### Phase 4: Web Interface (Optional)

- **Task 4.1: FastAPI Setup:** Create a FastAPI application to expose the agent as a web service.
- **Task 4.2: Frontend:** Build a simple frontend (e.g., using HTML, CSS, and JavaScript) to interact with the agent.

## 5. Getting Started

To begin, we will create the `GEMINI.md` file with this plan. Then we will proceed with Phase 1.
