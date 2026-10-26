# PART D: RESTful API Design

**REST** (Representational State Transfer) ek **design style** hai, koi library nahi. Asal khayal ye hai ke duniya ko **resources** (cheezon) ki shakal mein dekho, aur un par HTTP methods se kaam karo.

## D.1 REST ke qawaid
1. **URL mein naam (noun), kaam method mein (verb)**
2. **Plural naam:** `/orders`, `/products`
3. **Hierarchy:** `/customers/5/orders` (customer 5 ke orders)
4. **Stateless:** har request mein poori info (auth waghera)
5. **Sahi status codes** (Part B.3)
6. **Ek jaisa JSON format** success aur errors dono ke liye
7. **Versioning:** `/v1/...`, taake purane clients na tootein

| ❌ Bura | ✅ REST | Kyun |
|---|---|---|
| `GET /getAllOrders` | `GET /orders` | Verb URL mein nahi |
| `GET /order/1042` | `GET /orders/1042` | Plural |
| `POST /createOrder` | `POST /orders` | Method khud "create" hai |
| `POST /orders/1042/delete` | `DELETE /orders/1042` | Sahi method |
| `GET /orders?customerId=5` | `GET /customers/5/orders` | Dono theek, nested zyada saaf |
| `POST /updateStatus` | `PATCH /orders/1042` + `{"status": "shipped"}` | Resource par partial update |
| `GET /deleteUser?id=5` 😱 | `DELETE /users/5` | GET kabhi kuch na badle (crawlers/prefetch!) |

**Actions jo CRUD mein fit nahi hote:** kabhi kabhi verb chalta hai, lekin resource ke **neeche** rakhein: `POST /orders/1042/cancel`, `POST /chat/completions`. OpenAI ki API bhi aisi hi hai.

## D.2 Misal: Store API ka design

| Method | Endpoint | Kaam | Success |
|---|---|---|---|
| `GET` | `/v1/products?category=&max_price=&limit=&offset=` | Products list (filter + pagination) | 200 |
| `GET` | `/v1/products/{id}` | Ek product | 200 / 404 |
| `POST` | `/v1/orders` | Order banao | 201 + `Location` |
| `GET` | `/v1/orders/{id}` | Order dekho | 200 / 404 |
| `PATCH` | `/v1/orders/{id}` | Status badlo | 200 |
| `POST` | `/v1/orders/{id}/cancel` | Cancel action | 200 / 409 (pehle hi deliver) |
| `GET` | `/v1/customers/{phone}/orders` | Customer ke orders | 200 |
| `POST` | `/v1/chat` | Bot se sawal | 200 |
| `POST` | `/v1/webhooks/whatsapp` | WhatsApp ka webhook | 200 |

## D.3 Pagination
List endpoints kabhi **saara** data ek saath na lautayein (10 lakh orders = server crash).

| Tareeqa | URL | Fayda | Nuqsan |
|---|---|---|---|
| **Offset/limit** | `?limit=20&offset=40` | Aasan, page number pe jump | Bari tables par slow, beech mein naya data aaye to duplicate/miss |
| **Cursor** | `?limit=20&cursor=eyJpZCI6...` | Tez, stable (Shopify, Slack, Stripe) | Seedha page 50 par nahi ja sakte |

Response mein metadata dein: `total`, `limit`, `offset`, ya `next_cursor`.

▶ `python -m part_d_rest_design.d3_pagination` (server chalna chahiye)

## D.4 Error format: hamesha ek jaisa
Client ko har error ek hi shakal mein mile, taake woh ek hi jagah handle kar sake:
```json
{"error": {"code": 404, "message": "Order 1042 nahi mila", "request_id": "a1b2c3"}}
```
- **Kabhi stack trace, SQL query, ya file paths client ko na dikhayein** (security risk). Woh sirf **logs** mein jayein
- `request_id` se client support ko bata sakta hai, aur aap logs mein dhoond sakte hain

Part G.5 (`g05_error_handlers.py`) mein FastAPI se ye banayein ge.
