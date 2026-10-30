import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from mcp import Client
from mcp.types import TextContent, TextResourceContents
from langchain.mcp import MCPAdapter
from langchain.agents import create_agent
from langchain_groq import ChatGroq

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / '.env')
URLS = {'travel': 'http://127.0.0.1:8001/mcp',
        'policy': 'http://127.0.0.1:8002/mcp',
        'work': 'http://127.0.0.1:8003/mcp'}

def as_text(result) -> str:
    return '\n'.join(x.text for x in result.contents if isinstance(x, TextResourceContents))

async def load_context():
    async with Client(URLS['travel']) as c:
        preferences = as_text(await c.read_resource('travel://preferences'))
        guide = as_text(await c.read_resource('city://Dubai/guide'))
        p = await c.get_prompt('plan_business_trip', {'destination': 'Dubai', 'days': '5'})
        instruction = '\n'.join(m.content.text for m in p.messages if isinstance(m.content, TextContent))
    async with Client(URLS['policy']) as c:
        policy = as_text(await c.read_resource('policy://travel-summary'))
    return preferences, guide, instruction, policy

async def main():
    if not os.getenv('GROQ_API_KEY'):
        raise RuntimeError('GROQ_API_KEY missing in MCP_Practical/.env')
    preferences, guide, instruction, policy = await load_context()
    system_prompt = f'''You are a business trip assistant. Reply in easy Roman Urdu.
Traveler preferences (demo):\n{preferences}
City guide (illustrative):\n{guide}
MCP planning prompt:\n{instruction}
Demo company policies (policy source text):\n{policy}
Rules:
- Use travel_get_live_weather to retrieve current weather, and report unavailable results honestly.
- Use travel_search_flights for SAMPLE flight data (not actual inventory).
- Use policy_search_company_policy for SEMANTIC RAG retrieval of relevant company rules. Cite retrieved chunk_id and source in final answer; if retrieval fails, say so.
- Use travel_calculate_budget to add sample flight price and hotel estimate (45000 PKR total).
- Create ONE demonstration task with work_create_trip_task only because user explicitly requests task creation.
- Policy hotel's 12000 INR/night is in different currency: do not compare directly to PKR without currency conversion.
- Never imply a real booking, real company task, or live flight reservation.
- Booking tools are intentionally NOT available to you; you may only recommend a booking.
- Give concise final answer.'''
    config = {'mcpServers': {name: {'url': url} for name, url in URLS.items()}}
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        print('DISCOVERED TOOLS:', [tool.name for tool in tools])
        agent = create_agent(model=ChatGroq(model='openai/gpt-oss-20b', temperature=0),
                             tools=tools, system_prompt=system_prompt)
        question = ('Plan a 5-day business trip Lahore to Dubai. Check live Dubai weather, '
                    'find a sample flight, use semantic policy search to check economy, hotel and reimbursement rules, '
                    'calculate combined demo flight and 45000 PKR hotel estimate, '
                    'and create one demo preparation task titled Prepare Dubai meeting agenda. '
                    'Clearly label sample data and current weather observation time.')
        result = await agent.ainvoke({'messages': [{'role': 'user', 'content': question}]})
        print('\nMESSAGE FLOW:')
        for message in result['messages']:
            print('\n', type(message).__name__)
            for call in getattr(message, 'tool_calls', []) or []:
                print('TOOL:', call['name'], 'ARGS:', call['args'])
            print('CONTENT:', message.content)
        print('\nFINAL ANSWER:\n', result['messages'][-1].content)
        print('\nSECURITY: Booking service is excluded from autonomous agent tools.')

if __name__ == '__main__':
    asyncio.run(main())
