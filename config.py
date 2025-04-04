from sub_graphs.swe.project_data_state import FileState
from utils.logger import BRDLogger, LogLevel
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from copilotkit.langchain import copilotkit_customize_config
from dotenv import load_dotenv

# from langchain_deepseek import ChatDeepSeek
from langchain_anthropic import ChatAnthropic


# Initialize components
load_dotenv(".env")
logger = BRDLogger()

llm = ChatAnthropic(
    model="claude-3-7-sonnet-20250219", max_tokens=5000, temperature=0.5
)
# llm = ChatDeepSeek(temperature=0.5, model="deepseek-reasoner")
llm_mini = ChatOpenAI(temperature=0.5, model="gpt-4o-mini")


logger = BRDLogger()


# Retry decorator for AI calls
# @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_ai(request, input_data, config):
    """Wrapper for AI calls with retry mechanism."""
    try:
        return await request.ainvoke(input_data, customize_config(config))
    except Exception as e:
        logger.log(f"AI call failed, retrying: {str(e)[:50]}", level=LogLevel.WARNING)
        raise


def customize_config(config: RunnableConfig) -> RunnableConfig:
    """Customize LangChain config for CopilotKit."""
    return copilotkit_customize_config(
        config,
        emit_messages=False,
        # emit_tool_calls=True,
    )
