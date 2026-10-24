from crewai.flow.flow import Flow, start, listen, router
import random

# create a flow class
class MyRouterFlow(Flow):
    
    # define a start method
    @start()
    def input_node(self) -> bool:
        random_output = random.choice([True, False])
        # add output to state
        self.state["output"] = random_output
        return random_output
    
    # define the router node
    @router(input_node)
    def router_node(self) -> str:
        if self.state["output"]:
            return "success"
        else:
            return "failure"
        
    @listen("success")
    def sucess_node(self) -> str:
        return "Flow is Success"
    
    @listen("failure")
    def failure_node(self) -> str:
        return "Flow is a Failure"
    
if __name__ == "__main__":
    flow = MyRouterFlow()
    
    # execute the flow and print output
    response = flow.kickoff()
    print(f"Flow Output: {response}")
    
    # plot the flow
    # flow.plot("router_flow.html")
    
    # print the state
    print(flow.state)