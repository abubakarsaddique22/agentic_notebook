#!/usr/bin/env python
import warnings
from knowledge_crew.crew import KnowledgeCrew
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    inputs = {
        'query': 'What is the Abstract of the paper talking about?',
    }

    try:
        KnowledgeCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")