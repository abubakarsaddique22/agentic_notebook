#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from news_report_crew.crew import NewsReportCrew
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    inputs = {
        'country': 'pakistan',
    }

    try:
        NewsReportCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")