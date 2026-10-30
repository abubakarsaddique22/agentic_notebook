import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import httpx2
from booking_client import authenticated_booking_client, URL
load_dotenv(Path(__file__).resolve().parent.parent/'.env')
async def main():
    async with httpx2.AsyncClient() as http:
        r=await http.post(URL,json={'jsonrpc':'2.0','id':1,'method':'ping'},headers={'Accept':'application/json, text/event-stream','Content-Type':'application/json'})
        print('No bearer auth HTTP status:',r.status_code,'(expected 401)')
        assert r.status_code==401
    async with authenticated_booking_client('traveler') as client:
        print('AUTHENTICATED TOOLS:',[t.name for t in (await client.list_tools()).tools])
        denied=await client.call_tool('execute_approved_booking',{'request_id':'invalid-test-request'})
        print('Traveler execute denied:',denied.is_error or 'Forbidden' in str(denied.content))
        assert denied.is_error or 'Forbidden' in str(denied.content)
    print('SECURITY SMOKE TEST PASSED')
if __name__=='__main__':asyncio.run(main())
