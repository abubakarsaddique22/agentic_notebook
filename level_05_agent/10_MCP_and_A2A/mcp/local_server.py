from fastmcp import FastMCP

mcp = FastMCP('my local mcp server')

@mcp.tool()
def add_number(a: int,b: int) -> int:
    """
    Add two number
    """
    return a+b 

@mcp.tool()
def subtract_number(a: int,b: int) -> int:
    """
    subtract two number 
    """
    return a - b

@mcp.tool()
def Multiply_number(a: int,b: int) -> int:
    """
    Multiply two number 
    """
    return a * b

@mcp.tool()
def divided_number(a: int,b: int) -> int:
    """
    divided two number 
    """
    return a / b

@mcp.tool()
def calculate_square(number: int) -> int:
    """Calculate the square of a number."""
    return number * number

def get_user_name() -> str:
    """Return a demo user name."""
    return "Abubakar"

if __name__ == "__main__":
    mcp.run()