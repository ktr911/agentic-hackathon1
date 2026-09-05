"""ADK application entry point."""

from google.adk.apps import App

from .geology.agent import geology_research_agent
from .root.agent import root_agent
from .tour.agent import tourism_research_agent


app = App(name="agent", root_agent=root_agent)

__all__ = [
    "app",
    "geology_research_agent",
    "root_agent",
    "tourism_research_agent",
]
