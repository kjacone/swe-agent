from pydantic import BaseModel, Field
from langchain.tools import tool


class SummarizeInput(BaseModel):
    """Input for the summarize tool"""

    markdown: str = Field(
        description="""
                          The markdown formatted summary of the final result.
                          If you add any headings, make sure to start at the top level (#).
                          """
    )


@tool(args_schema=SummarizeInput)
def SummarizeTool(summary: str):  # pylint: disable=invalid-name,unused-argument
    """
    Summarize the final result. Make sure that the summary is complete and
    includes all relevant information.
    """
