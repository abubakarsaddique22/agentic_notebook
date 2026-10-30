"""Human approval flow; model never receives approve/execute tools."""
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from booking_client import authenticated_booking_client
from mcp.types import TextContent
import json
load_dotenv(Path(__file__).resolve().parent.parent/'.env')

def unpack(result):
    if result.is_error: raise RuntimeError('MCP tool returned error')
    if result.structured_content:
        data=result.structured_content
        if 'result' in data and isinstance(data['result'],dict): return data['result']
        return data
    for item in result.content:
        if isinstance(item,TextContent):
            val=json.loads(item.text)
            if isinstance(val,dict): return val
    raise RuntimeError('No structured result')

async def main():
    city=input('City [Dubai]: ').strip() or 'Dubai'
    nights=int(input('Nights [5]: ').strip() or '5')
    async with authenticated_booking_client('traveler') as client:
        requested=unpack(await client.call_tool('request_hotel_booking',{'city':city,'nights':nights,'hotel_class':'4-star'}))
    print('PENDING REQUEST:',requested)
    if not requested.get('success'): return
    rid=requested['request_id']
    print('Demo action only; NO real booking or payment will occur.')
    answer=input('Are you the authorized approver? Type APPROVE to authorize or anything else to reject: ').strip()
    # This CLI input is only a demo approval UI. Real approval needs distinct logged-in approver identity.
    async with authenticated_booking_client('admin') as admin:
        decision=unpack(await admin.call_tool('approve_booking',{'request_id':rid,'approved':answer=='APPROVE'}))
        print('DECISION:',decision)
        if decision.get('status')=='approved':
            confirm=input('Type EXECUTE for the one-time DEMO booking: ').strip()
            if confirm=='EXECUTE':
                outcome=unpack(await admin.call_tool('execute_approved_booking',{'request_id':rid}))
                print('BOOKING RESULT:',outcome)
            else: print('Not executed.')

if __name__=='__main__': asyncio.run(main())
