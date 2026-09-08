
# get method

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def customers(customer_id: int):
    return {
        "customer_id": customer_id,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "status": "active",
        "created_at": "2023-01-01T12:00:00Z"
        }



# post method 

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Loneapplication(BaseModel):
    age : int
    income : float 
    lone_amount : float
    employment_year : int


@app.post("/predict/")
async def predict(data: Loneapplication):
    if data.income >50000 and data.employment_year:
        decision = "Approved"
    else:
        decision = "Rejected"
    return {
        "age": data.age,
        "decision": decision
        }
    

    

# path parameter --> ja wali information ko path me bhejna hai aur path ma he jati ha 
# first e.g 
from fastapi import FastAPI


app = FastAPI()
customer_risk_profile = {
    "101": {"name": "Alice", "risk_score": 75},
    "102": {"name": "Bob", "risk_score": 45},
    "103": {"name": "Charlie", "risk_score": 90},
    "104": {"name": "David", "risk_score": 60}
}


@app.get("/risk-profile/{customer_id}")
def get_risk_profile(customer_id: str):
    if customer_id in customer_risk_profile:
        return customer_risk_profile[customer_id]
    return {"error": "Customer not found"}

# second e.g 
from fastapi import FastAPI


app = FastAPI()

customer_risk_profile = {
    "101": {"name": "Alice", "risk_score": 75},
    "102": {"name": "Bob", "risk_score": 45},
    "103": {"name": "Charlie", "risk_score": 90},
    "104": {"name": "David", "risk_score": 60}
}


@app.get("/risk-profile/{customer_id}/risk-profile/{customer_name}")
def get_risk_profile(customer_id: str, customer_name: str):
    if customer_id in customer_risk_profile:
        customer = customer_risk_profile[customer_id]
        if customer["name"] == customer_name:
            return customer
    return {"error": "Customer not found"}

# query parameter --> ja wali information ko query me bhejna hai aur query ma he jati ha aur bus asa ma hum
# additional information bhej sakte ha jaise ki filter, sort, pagination etc.

from fastapi import FastAPI

app = FastAPI()

all_customer = [
    {"id": "101", "name": "Alice", "city": "New York", "risk_score": 75},
    {"id": "102", "name": "Bob", "city": "Los Angeles", "risk_score": 45},
    {'id': "103", "name": "Charlie", "city": "Chicago", "risk_score": 90},
    {"id": "104", "name": "David", "city": "Houston", "risk_score": 60}
]


# query parameter 
@app.get("/risk-profile/")
def get_risk_profile(city: str = None, min_risk_score: int = None):
    filtered_customers = all_customer
    if city:
        filtered_customers = [customer for customer in filtered_customers if customer["city"] == city]
    if min_risk_score is not None:
        filtered_customers = [customer for customer in filtered_customers if customer["risk_score"] >= min_risk_score]
    return filtered_customers





# excetion handling in fastapi 
from fastapi import FastAPI , HTTPException

app = FastAPI()

students ={
    "s001": {"name": "Alice", "marks": 20, "major": "Computer Science"},
    "s002": {"name": "Bob", "marks": 15, "major": "Mathematics"},
    "s003": {"name": "Charlie", "marks": 18, "major": "Physics"},
    "s004": {"name": "David", "marks": 22, "major": "Chemistry"}
}

@app.get("/students/{student_id}")
def get_student(student_id: str):
    try:
      if student_id in students:
         return students[student_id]

    except KeyError:
        raise HTTPException(status_code=404, detail="Student not found")