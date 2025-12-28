import os

from dotenv import load_dotenv
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

# Import our tools
from tools.weather import get_weather_by_prompt
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def create_weekend_planner_agent():
    tools = [
        get_weather_by_prompt
    ]

    # create a simple tool-using agent
    model = ChatOpenAI(
        model="gpt-5-nano",
        temperature=0.1,
        max_tokens=None,
        timeout=30,
        api_key=OPENAI_API_KEY
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a weekend planner."),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad")
    ])
    agent = create_tool_calling_agent(model, tools=tools, prompt=prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # run the agent
    result = executor.invoke({"input" : "Plan my Saturday in Seattle"})

    print(result)

if __name__ == "__main__":
    create_weekend_planner_agent()