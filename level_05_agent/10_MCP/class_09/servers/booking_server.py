"""Protected DEMO booking MCP service on :8004. No real hotel integration."""
import os
import hmac
import sqlite3
import secrets
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pydantic import AnyHttpUrl
from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.auth.middleware.auth_context import get_access_token

load_dotenv(Path(__file__).resolve().parents[1] / '.env')
RESOURCE = os.getenv('BOOKING_RESOURCE_URL', 'http://booking:8004/mcp')
DB = Path(os.getenv('BOOKING_DB_PATH', '/app/state/approvals.db'))
USER_TOKEN = os.getenv('BOOKING_USER_TOKEN', '')
ADMIN_TOKEN = os.getenv('BOOKING_ADMIN_TOKEN', '')
if not USER_TOKEN or not ADMIN_TOKEN or USER_TOKEN == ADMIN_TOKEN:
    raise RuntimeError('Set distinct BOOKING_USER_TOKEN and BOOKING_ADMIN_TOKEN')

class DemoVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        if hmac.compare_digest(token, USER_TOKEN):
            return AccessToken(token=token, client_id='traveler', scopes=['booking:read'], resource=RESOURCE)
        if hmac.compare_digest(token, ADMIN_TOKEN):
            return AccessToken(token=token, client_id='booking-admin', scopes=['booking:read','booking:approve','booking:execute'], resource=RESOURCE)
        return None

server = MCPServer(
    'Secured Demo Booking MCP',
    token_verifier=DemoVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl('https://auth.example.com'),  # Documentation placeholder, NOT a live identity provider
        resource_server_url=AnyHttpUrl(RESOURCE),
        required_scopes=['booking:read'],
        validate_token_resource=True,
    ),
)

def connection():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.execute("""CREATE TABLE IF NOT EXISTS approvals (
        id TEXT PRIMARY KEY, city TEXT NOT NULL, nights INTEGER NOT NULL,
        hotel_class TEXT NOT NULL, status TEXT NOT NULL, expires_at TEXT NOT NULL,
        booking_id TEXT, requested_by TEXT NOT NULL)""")
    con.commit()
    return con

def principal(required: str):
    token = get_access_token()
    if token is None or required not in token.scopes:
        raise PermissionError(f'Forbidden: {required} scope required')
    return token.client_id

@server.tool()
def request_hotel_booking(city: str, nights: int, hotel_class: str = '4-star') -> dict:
    """Create a pending DEMO booking request. Never books a hotel."""
    caller = principal('booking:read')
    city = city.strip()
    if not (2 <= len(city) <= 80) or not (1 <= nights <= 30) or hotel_class not in {'3-star','4-star','5-star'}:
        return {'success':False,'error':'Invalid city/nights/hotel_class'}
    request_id = secrets.token_urlsafe(24)
    expires = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    with connection() as con:
        con.execute('INSERT INTO approvals (id,city,nights,hotel_class,status,expires_at,requested_by) VALUES (?,?,?,?,?,?,?)',
                    (request_id,city,nights,hotel_class,'pending',expires,caller))
    return {'success':True,'request_id':request_id,'status':'pending','city':city,'nights':nights,'hotel_class':hotel_class,'expires_at':expires,'demo':True}

@server.tool()
def get_booking_request(request_id: str) -> dict:
    """Read a booking request; traveler sees only requests they created."""
    token = get_access_token()
    caller = principal('booking:read')
    with connection() as con:
        row = con.execute('SELECT id,city,nights,hotel_class,status,expires_at,booking_id,requested_by FROM approvals WHERE id=?',(request_id,)).fetchone()
    if not row or (caller != row[7] and 'booking:approve' not in token.scopes):
        return {'success':False,'error':'Not found or forbidden'}
    return {'success':True,'request_id':row[0],'city':row[1],'nights':row[2],'hotel_class':row[3],'status':row[4],'expires_at':row[5],'booking_id':row[6],'demo':True}

@server.tool()
def approve_booking(request_id: str, approved: bool) -> dict:
    """ADMIN ONLY. Authorize or reject a pending demo request."""
    principal('booking:approve')
    now = datetime.now(timezone.utc)
    with connection() as con:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute('SELECT status,expires_at FROM approvals WHERE id=?',(request_id,)).fetchone()
        if not row or row[0]!='pending': return {'success':False,'error':'No pending request'}
        if datetime.fromisoformat(row[1]) <= now:
            con.execute("UPDATE approvals SET status='expired' WHERE id=?",(request_id,))
            return {'success':False,'error':'Request expired'}
        status='approved' if approved else 'rejected'
        con.execute('UPDATE approvals SET status=? WHERE id=?',(status,request_id))
    return {'success':True,'request_id':request_id,'status':status,'demo':True}

@server.tool()
def execute_approved_booking(request_id: str) -> dict:
    """ADMIN ONLY. One-time, approved, DEMO execution. No real vendor call."""
    principal('booking:execute')
    with connection() as con:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute('SELECT city,nights,hotel_class,status,expires_at FROM approvals WHERE id=?',(request_id,)).fetchone()
        if not row or row[3]!='approved': return {'success':False,'error':'Missing approval or already executed'}
        if datetime.fromisoformat(row[4]) <= datetime.now(timezone.utc):
            con.execute("UPDATE approvals SET status='expired' WHERE id=?",(request_id,))
            return {'success':False,'error':'Approval expired'}
        booking_id='DEMO-'+secrets.token_hex(6).upper()
        updated=con.execute("UPDATE approvals SET status='executed',booking_id=? WHERE id=? AND status='approved'",(booking_id,request_id)).rowcount
        if updated!=1: return {'success':False,'error':'Already consumed'}
    return {'success':True,'status':'executed','booking_id':booking_id,'city':row[0],'nights':row[1],'hotel_class':row[2],'demo':True,'real_booking':False}

if __name__=='__main__':
    server.run(transport='streamable-http',host='0.0.0.0',port=8004,stateless_http=True,json_response=True)
