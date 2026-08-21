#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from blog_genration_crew.crew import BlogGenrationCrew
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': "Impact of AI Agents on Software Development",
    }

    try:
        BlogGenrationCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
