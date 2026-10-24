from crewai.flow.flow import Flow, start, listen


# define my custom flow class
class MyFirstFlow(Flow):
    
    # define the start_node/trigger_node
    @start()
    def start_flow(self) -> str:
        return "Flow Started Successfully"
    
    # make the second node and connect to the first node
    @listen(start_flow)
    def processing_node(self, node_output) -> str:
        print(f"Output from Start Node: {node_output}")
        return "Data Process Complete"
    
    # make a third node and connect to the second node
    @listen(processing_node)
    def flow_complete(self, node_output_2) -> str:
        print(f"Output from Processing Node: {node_output_2}")
        return "Flow Execution Complete"
    
    
if __name__ == "__main__":
    # create the flow
    flow = MyFirstFlow()
    
    # output returned by the last node of the flow
    # execute the flow
    result = flow.kickoff()
    
    # plot the flow
    flow.plot("first_flow.html")
    
    # print the result
    print(f"Flow Result: {result}")