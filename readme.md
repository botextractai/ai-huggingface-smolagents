# Code Agents with the HuggingFace Smolagents AI Agent Framework

Tool-calling agents use Large Language Models (LLMs) to write out multiple function calls sequentially to complete a complex sequence of tasks. They generate one function call, execute it, observe, reason, and then decide what to do next. Code agents take a different approach. They consolidate all these calls into a single block or snippet of code, letting the LLM lay out an entire plan of action at once. That block can be executed efficiently, providing more reliable results.

This example shows how to create code agents with [Smolagents](https://smolagents.org/), a lightweight agentic framework from [Hugging Face](https://huggingface.co/) designed specifically for code agents that write their actions in program code. Code agents are often more efficient, because they usually require less LLM calls and processing steps, such as tool calls. This often reduces latency, costs, and error rates. In addition to code agents, Smolagents also supports traditional tool-calling agents, where actions are written as JSON or text blocks, suitable for specific scenarios and requirements.

This example uses this team of agents (output from `manager_agent.visualize()`):

```
CodeAgent | gpt-4o
├── ✅ Authorized imports: ['geopandas', 'plotly',
│   'plotly.express', 'plotly.express.colors', 'shapely', 'json',
│   'pandas', 'numpy']
├── 🛠️ Tools:
│   ┌──────────────┬──────────────────────┬──────────────────────┐
│   │ Name         │ Description          │ Arguments            │
│   ├──────────────┼──────────────────────┼──────────────────────┤
│   │ final_answer │ Provides a final     │ answer (`any`): The  │
│   │              │ answer to the given  │ final answer to the  │
│   │              │ problem.             │ problem              │
│   └──────────────┴──────────────────────┴──────────────────────┘
└── 🤖 Managed agents:
    └── web_agent | CodeAgent | gpt-4o
        ├── ✅ Authorized imports: []
        ├── 📝 Description: Runs web searches for you.
        └── 🛠️ Tools:
            ┌───────────────┬──────────────────┬─────────────────┐
            │ Name          │ Description      │ Arguments       │
            ├───────────────┼──────────────────┼─────────────────┤
            │ web_search    │ Searches the web │ query           │
            │               │ for your query.  │ (`string`):     │
            │               │                  │ Your query      │
            │ visit_webpage │ Visits a webpage │ url (`string`): │
            │               │ at the given url │ The url of the  │
            │               │ and reads its    │ webpage to      │
            │               │ content as a     │ visit.          │
            │               │ markdown string. │                 │
            │               │ Use this to      │                 │
            │               │ browse webpages. │                 │
            │ final_answer  │ Provides a final │ answer (`any`): │
            │               │ answer to the    │ The final       │
            │               │ given problem.   │ answer to the   │
            │               │                  │ problem         │
            └───────────────┴──────────────────┴─────────────────┘
```

This example builds a research multi-agent system that can find information online and organise it into a geographical map using [Plotly](https://plotly.com/dash/plotly-ai/).

It uses the Tavily API to browse the web for the 10 most populated cities in the world, along with their population count, and their approximate daily temperature in December. The contents from the retrieved web pages gets extracted as markdown strings.

The Plotly geographical map gets saved as a file called "saved_map.png" to the project root folder.

![alt text](https://github.com/user-attachments/assets/9f4512d3-fa39-43a5-94cf-69b568f8cbc7 "Plotly Map")

## Secure code execution

Executing automatically generated program code can carry serious risks.

Smolagents uses a custom Python executor that has been built from scratch to be more secure. The Smolagents Python executor includes these built-in safeguards:

- Any undefined command is ignored
- Imports are secured, because any import outside of this white list must be explicitly allowed : `re`, `queue`, `random`, `statistics`, `unicodedata`, `itertools`, `math`, `stat`, `time`, `datetime`, `collections`, `numpy`
- Prevents infinite loops due to a maximum number of iterations

Security can be further improved by using sandboxes for code executions, such as local Docker containers, or [E2B](https://e2b.dev/) (Execution to Binary) sandboxes.

## Required API keys for this example

You need an OpenAI API key for this example. [Get your OpenAI API key here](https://platform.openai.com/login). Alternatively, you can also use other LLMs, including models hosted on the Hugging Face Hub via Transformers, as well as models from Anthropic and others through [LiteLLM](https://www.litellm.ai/) integration.

You also need a free Tavily API key for this example. [Get your free Tavily API key here](https://app.tavily.com/sign-in).

Insert both API keys into the `.env.example` file and then rename this file to just `.env` (remove the ".example" ending).
