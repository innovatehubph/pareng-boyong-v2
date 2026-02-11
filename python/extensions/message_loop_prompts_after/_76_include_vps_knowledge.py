"""
VPS Knowledge Extension for Pareng Boyong
Automatically loads VPS filesystem knowledge into the agent's context.

Created: 2026-02-03
"""

from python.helpers.extension import Extension
from agent import LoopData


class IncludeVPSKnowledge(Extension):
    """
    Adds VPS filesystem knowledge to Pareng Boyong's context.
    This helps the agent understand:
    - Where it's running (Docker container)
    - How to access VPS files (/vps mount)
    - Key directory locations
    - Brotherhood member locations
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Read the VPS knowledge prompt
        try:
            vps_knowledge = self.agent.read_prompt("agent.extras.vps_knowledge.md")

            # Add to temporary extras (included in context)
            loop_data.extras_temporary["vps_knowledge"] = vps_knowledge

        except Exception as e:
            # Don't fail silently but also don't crash
            self.agent.context.log.log(
                type="warning",
                content=f"Could not load VPS knowledge: {str(e)}"
            )
