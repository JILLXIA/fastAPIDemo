import os
from functools import lru_cache
import logging
import time
from typing import Any, Optional
import re

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
from langchain_core.callbacks import BaseCallbackHandler

from logging_utils import sanitize_for_log

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ToolLoggingCallbackHandler(BaseCallbackHandler):
    """Logs tool calls with inputs and truncated outputs.

    Option B behavior:
    - Always logs tool name + inputs (sanitized/truncated).
    - Logs outputs truncated (more detail when LOG_LEVEL=DEBUG).
    """

    def __init__(self, *, max_chars_info: int = 2000, max_chars_debug: int = 8000):
        self._max_info = max_chars_info
        self._max_debug = max_chars_debug
        self._starts: dict[str, float] = {}

    def _limit(self) -> int:
        return self._max_debug if logger.isEnabledFor(logging.DEBUG) else self._max_info

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        name = serialized.get("name") or serialized.get("id") or "<unknown_tool>"
        self._starts[str(run_id)] = time.perf_counter()
        logger.info(
            "tool start name=%s run_id=%s input=%s",
            name,
            run_id,
            sanitize_for_log(input_str, max_chars=self._limit()),
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        start = self._starts.pop(str(run_id), None)
        dur_ms = (time.perf_counter() - start) * 1000 if start else None
        logger.info(
            "tool end run_id=%s duration_ms=%s output=%s",
            run_id,
            f"{dur_ms:.2f}" if dur_ms is not None else "?",
            sanitize_for_log(output, max_chars=self._limit()),
        )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        logger.exception("tool error run_id=%s", run_id, exc_info=error)


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
            "IMPORTANT RULES:\n"
            "- This is a ONE-SHOT interaction. Never ask the user any questions.\n"
            "- Do NOT end your response with a question. Do NOT request preferences, confirmations, or follow-ups.\n"
            "- If information is missing or ambiguous, pick reasonable defaults and proceed.\n"
            "- If a tool returns no results or errors, provide a reasonable fallback suggestion without asking the user for more info.\n"
            "DEFAULT ASSUMPTIONS (use when not specified):\n"
            "- Dates: assume the upcoming Friday evening + Saturday + Sunday in the user's locale.\n"
            "- Pace: balanced (some sightseeing + one movie + one event).\n"
            "- Budget: mid-range.\n"
            "- Travel radius: within ~0-40 km (or ~20 minutes by car/transit) of city center.\n"
            "- Cuisine: broadly popular local options; if none, pick 5-6 varied choices (e.g., sushi, Italian, tacos).\n"
            "- Movies: pick 3 currently popular options and suggest showtime-check guidance (without asking questions).\n"
            "- Events: pick 3 relevant events with their URLs; if none, suggest common alternatives (live music venues, museums, parks).\n"
            "OUTPUT FORMAT:\n"
            "Return a single comprehensive plan with clear sections (Weather, Movies, Cinemas, Restaurants, Events, Suggested Itinerary).",
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

    logger.info(
        "building agent executor model=%s temperature=%s timeout_s=%s tools=%s",
        model_name,
        temperature,
        timeout_s,
        [getattr(t, "name", str(t)) for t in tools],
    )

    model = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=None,
        timeout=timeout_s,
        api_key=openai_api_key,
    )

    agent = create_tool_calling_agent(model, tools=tools, prompt=prompt)
    callbacks = [ToolLoggingCallbackHandler()]
    return AgentExecutor(agent=agent, tools=tools, verbose=verbose, callbacks=callbacks)


def _enforce_one_shot_output(text: str) -> str:
    """Ensure the agent returns a one-shot response (no follow-up questions).

    We do two things:
    - Strip trailing question-only lines.
    - If the last sentence is a question, replace it with a default-assumption line.

    This is a safety net on top of the system prompt.
    """
    if not text:
        return text

    lines = [ln.rstrip() for ln in text.splitlines()]
    # Drop empty tail
    while lines and not lines[-1].strip():
        lines.pop()

    # Remove obvious follow-up question lines at the end.
    while lines and lines[-1].strip().endswith("?"):
        lines.pop()

    out = "\n".join(lines).strip()
    if not out:
        return "Assumptions: I used reasonable defaults (balanced pace, mid-range budget, and nearby options) and provided a complete weekend plan in one message."

    # If the output still contains a final question mark, replace the final question-y sentence.
    if out.endswith("?"):
        out = re.sub(
            r"\?\s*$",
            ".",
            out,
        )

    # If any question remains anywhere, add an explicit note that assumptions were made.
    if "?" in out:
        out = out.replace("?", ".")
        out += (
            "\n\nAssumptions used: balanced pace, mid-range budget, within ~5–8 km of city center; "
            "please check showtimes/reservation availability in your preferred apps."
        )

    return out


def run_weekend_planner(query: str, *, verbose: bool = False) -> dict:
    """Run the weekend planner agent for a given user query.

    Returns the raw LangChain invoke result (typically includes 'output').
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")

    executor = get_weekend_planner_executor(verbose=verbose)
    start = time.perf_counter()
    result = executor.invoke({"input": query})
    dur_ms = (time.perf_counter() - start) * 1000
    logger.info("agent invoke complete duration_ms=%.2f", dur_ms)

    # Safety net: enforce one-shot output.
    if isinstance(result, dict) and isinstance(result.get("output"), str):
        result["output"] = _enforce_one_shot_output(result["output"])

    return result


if __name__ == "__main__":
    # Tiny manual smoke run
    user_query = "Plan my new years holiday in San Jose"
    result = run_weekend_planner(user_query, verbose=True)
    print(result)
