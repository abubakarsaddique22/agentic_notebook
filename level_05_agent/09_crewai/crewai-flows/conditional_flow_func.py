from crewai.flow.flow import Flow, start, listen, and_
from typing import Any

# create the flow
class MyConditionalFlow(Flow):
    
    # define the start node
    @start()
    def start_node(self) -> str:
        return "Flow Started"
    
    # define the second node
    @listen(start_node)
    def person_name(self) -> str:
        name = "Aman"
        # add the name to state
        self.state["name"] = name
        return name
    
    # define the third node
    @listen(start_node)
    def person_age(self) -> int:
        age = 25
        # add age to state
        self.state["age"] = age
        return age
    
    # define the fourth node
    @listen(and_(person_name, person_age))
    def person_info(self) -> dict[str, Any]:
        name = self.state["name"] 
        age = self.state["age"]
        person_dict = {
            "name": name,
            "age": age
        }
        return person_dict
    
if __name__ == "__main__":
    flow = MyConditionalFlow()
    
    # execute the flow
    result = flow.kickoff()
    
    # plot the flow
    flow.plot("conditional_flow.html")
    
    print(f"Flow Output: {result}")