"""
D.3 Pagination: saare pages loop mein laana
===========================================
Real kaam: kisi bhi API (Shopify, CRM) se poora data nikaalna.
    python -m part_d_rest_design.d3_pagination

Theory: part_d_rest_design/NOTES.md (D.3)
"""
from common import get_client

client = get_client()

offset, all_items = 0, []
while True:
    page = client.get("/products", params={"category": "watches", "limit": 2, "offset": offset}).json()
    all_items += page["items"]
    print(f"offset={offset}: {[p['name'] for p in page['items']]}")
    offset += page["limit"]
    if offset >= page["total"]:       # aakhri page aa gaya
        break

print("Kul watches:", len(all_items))
client.close()
