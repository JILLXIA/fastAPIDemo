# GEMINI.md - Weekend Planner Agent

This document outlines the plan and current status for building a Weekend Planner Agent.

## 1. Project Goal

The goal is to create an AI agent that helps users plan their weekend activities. The agent takes user preferences as input and generates a personalized weekend itinerary, leveraging external tools for real-time data.

## 2. Features

- **User Preference Input:** Natural language interface for users to specify location, interests, and constraints.
- **Activity Suggestions:** Suggests restaurants, cafes, and attractions using OpenStreetMap data.
- **Event Discovery:** Finds local events (concerts, sports, arts) using the Ticketmaster API.
- **Movie Recommendations:** Suggests currently playing or popular movies using the TMDB API.
- **Weather Forecast:** Checks weather conditions using OpenWeatherMap to ensure suitable activities.
- **Itinerary Generation:** Orchestrates all data into a cohesive, readable weekend plan.

## 3. Tech Stack

- **Language:** Python 3.11+
- **Core LLM:** OpenAI (GPT-4o / GPT-5-nano) via LangChain
- **Framework:** FastAPI (Web API)
- **Containerization:** Docker & Docker Compose
- **External APIs:**
    - **OpenWeatherMap:** Weather forecasts.
    - **OpenStreetMap (Overpass API):** Location-based suggestions (Restaurants, Amenities).
    - **Ticketmaster:** Event discovery.
    - **TMDB (The Movie Database):** Movie discovery.

## 4. Development Status

### Phase 1: Core Agent & Project Setup (✅ Completed)
- **Task 1.1: Project Scaffolding:** Set up Python project, `requirements.txt`, and directory structure.
- **Task 1.2: Basic Agent Logic:** Implemented LangChain agent with tool calling capabilities in `agent.py`.
- **Task 1.3: API Server:** set up `main.py` with FastAPI to expose the agent via HTTP endpoints.

### Phase 2: Tool Integration (✅ Completed)
- **Task 2.1: Weather Tool:** Implemented `tools/weather.py`.
- **Task 2.2: Places Tool:** Implemented `tools/places.py` using OpenStreetMap (replaced Google Places).
- **Task 2.3: Events Tool:** Implemented `tools/events.py` using Ticketmaster.
- **Task 2.4: Movie Tool:** Implemented `tools/movie.py` using TMDB (New addition).
- **Task 2.5: Geocoding Tool:** Implemented `tools/geocoding.py` to resolve city names to coordinates.

### Phase 3: Itinerary Generation & Output (✅ Completed)
- **Task 3.1: Structured Output:** Agent prompt (`agent.py`) configured to return structured plans (Weather, Movies, Dining, Events).
- **Task 3.2: Robustness:** Added safety nets for "one-shot" responses and error handling.
- **Task 3.3: Logging:** Implemented comprehensive logging (`logging_utils.py`) for requests and tool usage.

### Phase 4: Web Interface (🚧 In Progress)
- **Task 4.1: FastAPI Setup:** Expose agent as a web service. (✅ Completed)
- **Task 4.2: Frontend:** Build a simple frontend (HTML/CSS/JS) to interact with the agent. (TODO)

### Phase 5: Infrastructure & Quality (✅ Completed)
- **Task 5.1: Docker:** Created `Dockerfile` and `docker-compose.yml` for easy deployment.
- **Task 5.2: Testing:** Added unit tests (`test_main.py`, `test_event_tool.py`).

## 5. Getting Started

### Prerequisites
- Python 3.11+ or Docker
- API Keys for: OpenAI, OpenWeatherMap, Ticketmaster, TMDB.

### Running Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up environment variables in `.env` (see `.env.example` if available).
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Running with Docker
1. Build and run:
   ```bash
   docker-compose up --build
   ```

## 6. Future Improvements
- Implement a React/Streamlit frontend.
- Add user session history.
- Improve error handling for specific API quotas.