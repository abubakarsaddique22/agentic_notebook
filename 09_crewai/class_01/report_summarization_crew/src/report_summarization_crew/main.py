from report_summarization_crew.crew import ReportSummarizationCrew


def run():
    """it runs the report summarization crew"""
    # define the inputs
    inputs = {"field": "Education"}
    
    # create the crew
    my_crew = ReportSummarizationCrew().crew()
    
    # pass the inputs to the crew and execute the crew
    result = my_crew.kickoff(inputs=inputs)
    
    
if __name__ == "__main__":
    run()