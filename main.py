import os
import pandas as pd
import re
import requests
from dotenv import load_dotenv
from markdownify import markdownify
from PIL import Image
from requests.exceptions import RequestException
from smolagents import CodeAgent, OpenAIServerModel, tool, Tool     # tool=decorator | Tool=class
from smolagents.utils import encode_image_base64, make_image_url, truncate_content
from tavily import TavilyClient

import warnings
warnings.filterwarnings('ignore')

# Environment variables
load_dotenv()
openai_api_key = os.environ["OPENAI_API_KEY"]
tavily_api_key = os.environ["TAVILY_API_KEY"]


# SET UP THE SEARCH TOOL
# ======================

@tool
def web_search(query: str) -> str:
    """Searches the web for your query.

    Args:
        query: Your query
    """
    tavily_client = TavilyClient(api_key=tavily_api_key)
    response = tavily_client.search(query)
    return str(response["results"])


class VisitWebpageTool(Tool):
    name = "visit_webpage"
    description = (
        "Visits a webpage at the given url and reads its content as a markdown string. Use this to browse webpages."
    )
    inputs = {
        "url": {
            "type": "string",
            "description": "The url of the webpage to visit.",
        }
    }
    output_type = "string"

    def forward(self, url: str) -> str:
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()  # raise an exception for bad status codes
            markdown_content = markdownify(response.text).strip()
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
            return truncate_content(markdown_content, 40000)
        except requests.exceptions.Timeout:
            return "The request timed out. Please try again later or check the URL."
        except RequestException as e:
            return f"Error fetching the webpage: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


# SET UP AN AGENT
# ===============

model = OpenAIServerModel(
    model_id="gpt-4o",                      # OpenAI model ID
    api_base="https://api.openai.com/v1",   # default OpenAI endpoint
    api_key=openai_api_key,                 # OpenAI API key
    max_completion_tokens=8096
)

request_cities = """
Return a sorted list of the 10 most populated cities in the world, 
along with their population count (in millions with two decimal places), 
and their approximate daily temperature in December at their location.
"""

# "CodeAgent" is the main class of agents in the HuggingFace Smolagents AI Framework
agent = CodeAgent(
    model=model,
    tools=[web_search, VisitWebpageTool()],
    max_steps=10
)
agent.logger.console.width=66
result = agent.run(request_cities)

# handle case where agent doesn't return a Python list
try:
    print(pd.DataFrame(result))
except Exception as e:
    print("Could not display as DataFrame:", e)
    print(result)


# CREATE A MULTI-AGENT RESEARCHER
# ===============================

# Start with web search agent
# ---------------------------

web_agent = CodeAgent(
    model = OpenAIServerModel(
        model_id="gpt-4o",                      # OpenAI model ID
        api_base="https://api.openai.com/v1",   # default OpenAI endpoint
        api_key=openai_api_key,                 # OpenAI API key
        max_completion_tokens=8096
    ),
    tools=[web_search, VisitWebpageTool()],
    max_steps=10,
    name="web_agent",
    description="Runs web searches for you."
)
web_agent.logger.console.width=66

# Set up a manager agent
# ----------------------

def check_reasoning_and_plot(final_answer, agent_memory):
    final_answer
    multimodal_model = OpenAIServerModel(
        model_id="gpt-4o",                      # OpenAI model ID
        api_base="https://api.openai.com/v1",   # default OpenAI endpoint
        api_key=openai_api_key,                 # OpenAI API key
    )
    filepath = "saved_map.png"
    assert os.path.exists(filepath), "Make sure to save the plot under saved_map.png!"
    image = Image.open(filepath)
    prompt = (
        f"Here is a user-given task and the agent steps: {agent_memory.get_succinct_steps()}. Now here is the plot that was made."
        "Please check that the reasoning process and plot are correct: do they correctly answer the given task?"
        "First list reasons why yes/no, then write your final decision: PASS in caps lock if it is satisfactory, FAIL if it is not."
        "Don't be harsh: if the plot mostly solves the task, it should pass."
        "To pass, a plot should be made using px.scatter_map and not any other method (scatter_map looks nicer)."
        "Also, any run that invents numbers should fail."
    )
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {"url": make_image_url(encode_image_base64(image))},
                },
            ],
        }
    ]
    output = multimodal_model(messages).content
    print("Feedback: ", output)
    # tries again if "FAIL" is found
    if "FAIL" in output:
        raise Exception(output)
    return True

manager_agent = CodeAgent(
    model=OpenAIServerModel(
        model_id="gpt-4o",                      # OpenAI model ID
        api_base="https://api.openai.com/v1",   # default OpenAI endpoint
        api_key=openai_api_key,                 # OpenAI API key
        max_tokens=8096,
    ),
    tools=[],
    managed_agents=[web_agent],
    additional_authorized_imports=[
        "geopandas",
        "plotly",
        "plotly.express",
        "plotly.express.colors",
        "shapely",
        "json",
        "pandas",
        "numpy",
    ],
    planning_interval=5,
    verbosity_level=2,
    final_answer_checks=[check_reasoning_and_plot],
    max_steps=15,
)
manager_agent.logger.console.width=66

# show the manager agent structure
manager_agent.visualize()

# remove Plotly geographical map file if exits
os.path.exists("saved_map.png") and os.remove("saved_map.png")

manager_agent.run(f"""
{request_cities}

Then make me a spatial map of the world using px.scatter_map, with the biggest cities 
represented as scatter points of size depending on population count and color depending 
on the average temperature in December. 
Label all cities and ensure that the text of the labels don't overlap. 
The title of the map is "Top 10 most populated cities with December temperatures". 
The title must be on the top (y-coordinate) and be center (x-coordinate). 
Save the map to saved_map.png, then return it!

Here's an example of how to plot and return a map: 
import plotly.express as px
df = px.data.carshare()
fig = px.scatter_map(df, lat="centroid_lat", lon="centroid_lon", text="name", color="peak_hour",
     color_continuous_scale=px.colors.sequential.Magma_r, size_max=15, zoom=1)
fig.show()
final_answer(fig)

Do not invent any numbers! You must only use numbers sourced from the internet.
""")

fig = manager_agent.python_executor.state["fig"]
fig.update_layout(width=800, height=600)
fig.show()
