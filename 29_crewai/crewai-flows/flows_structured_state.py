from crewai.flow.flow import Flow, start, listen
from pydantic import BaseModel, Field

class PersonState(BaseModel):
    
    name: str = Field(description="name of the person", default="")
    age: int = Field(description="age of the person", default=0)
    friends_list: list[str] = Field(description="Friends list of the person", default_factory=list)
    contact_info: dict[str, str|int] = Field(description="Person's contact information", default={})


# define the flow
class MyStructuredState(Flow[PersonState]):
    
    # define the start node
    @start()
    def get_inputs(self):
        # the structured state will be a pydantic model
        print(f"State: {self.state}")
        return self.state
    
    # define the second node
    @listen(get_inputs)
    def update_state(self):
        # friends list
        print("Original Friends List: ")
        for ind, friend in enumerate(self.state.friends_list, start=1):
            print(f"{ind}. {friend}")
        
        # changes in the friends list
        self.state.friends_list.remove("Rahul")
        print("Updated Friend's List: ")
        for ind, friend in enumerate(self.state.friends_list, start=1):
            print(f"{ind}. {friend}")
            
        # original mail id
        print("Original Email_id: ", self.state.contact_info["email_id"])
        # update the mail id
        self.state.contact_info["email_id"] = "amit123@gmail.com"
        print("Updated Email_id: ", self.state.contact_info["email_id"])
        
        return "State updated"
 
    
if __name__ == "__main__":
    # define the flow
    flow = MyStructuredState()
    
    # kickoff the flow
    output = flow.kickoff({
        "name": "Amit",
        "age": 35,
        "friends_list": ["Neha", "Hemant", "Rahul", "Priya"],
        "contact_info": {"email_id": "amit12345@gmail.com"}
    })
    
    # print the output
    print(f"Flow Output {output}")
    
    # print the state
    print(f"Flow State Dict: {flow.state.model_dump()}")