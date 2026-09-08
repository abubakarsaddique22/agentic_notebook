from crewai.flow.flow import Flow, start, listen
from typing import Any

# define the flow class
class MyUnstructuredStateFlow(Flow):
    
    # define the start node
    @start()
    def get_inputs(self) -> dict[str, Any]:
        # to access the state --> use self.state
        # unstructured state is in the form of dict {}
        print("Original state ", self.state)
        return self.state
    
    @listen(get_inputs)
    def update_state(self, last_output) -> str:
        # print("My state ", last_output, type(self.state))
        self.state["name"] = "Aman"
        self.state["age"] = 25
        self.state["friends_list"] = ["Neha", "Rahul", "Shobhit"]
        self.state["contact_info"] = {
            "email_id": "aman123@gmail.com",
            "mob": 7659934762
        }
        print("Updated State ", self.state)
        return "State Updated"
      
if __name__ == "__main__":
    # create the flow
    flow = MyUnstructuredStateFlow()
    
    # execute the flow
    output = flow.kickoff({
        "roll_no.": 1,
        "college_name": "Delhi University"
    })
    
    print(f"Flow Output: {output}")