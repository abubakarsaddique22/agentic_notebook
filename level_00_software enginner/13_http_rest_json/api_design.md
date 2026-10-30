# REST API Design Practice — Watch Store

Socho tumhari watch store ka apna backend hai. Neeche resources ke endpoints design karne hain.
Pehla resource (Products) example ke tor pe bhara hua hai — baaki khud bharo.

**Rules yaad rakho:**
- URL = noun (plural), Method = verb
- Path param = kaunsi cheez, Query param = filter/sort/page
- Sahi status code: create → 201, not found → 404, validation fail → 400/422, duplicate → 409

---

## ✅ Example: Products

| Method | Endpoint | Kaam | Success | Errors |
|---|---|---|---|---|
| GET | `/products` | Saari watches (filter: `?brand=casio&in_stock=true&page=2`) | 200 | — |
| GET | `/products/{id}` | Ek watch | 200 | 404 |
| POST | `/products` | Nayi watch add | 201 | 400, 401, 409 (same SKU) |
| PATCH | `/products/{id}` | Price/stock update | 200 | 400, 401, 404 |
| DELETE | `/products/{id}` | Watch hatao | 204 | 401, 404 |

**POST /products — request body:**
```json
{
  "name": "Casio Edifice EFR-526",
  "brand": "casio",
  "price": 18500,
  "sku": "CAS-EFR526",
  "in_stock": true
}
```

**201 response:**
```json
{
  "id": 42,
  "name": "Casio Edifice EFR-526",
  "brand": "casio",
  "price": 18500,
  "sku": "CAS-EFR526",
  "in_stock": true,
  "created_at": "2026-10-30T15:30:00Z"
}
```

**404 response (errors bhi consistent JSON):**
```json
{ "error": "not_found", "message": "Product 999 does not exist" }
```

---

## 🏋️ Tumhari baari

### 1. Orders
COD order banana, list, ek order, status update (pending → confirmed → shipped → delivered), cancel.

| Method | Endpoint | Kaam | Success | Errors |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |

POST body likho:
```json

```

**Socho:** Cancel ke liye `DELETE /orders/{id}` behtar hai ya `PATCH /orders/{id}` with `{"status": "cancelled"}`? Kyun?

### 2. Customers
Customer banana, ek customer, uske saare orders.

| Method | Endpoint | Kaam | Success | Errors |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

### 3. Reviews (nested resource)
Kisi product ke reviews dekhna aur naya review dena.

| Method | Endpoint | Kaam | Success | Errors |
|---|---|---|---|---|
| | | | | |
| | | | | |

### 4. Bonus — AI chatbot backend
Tumhare WhatsApp bot jaisa: user message bhejta hai, bot jawab deta hai, conversation history save hoti hai.

| Method | Endpoint | Kaam | Success | Errors |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

**Socho:** `POST /chat` idempotent hai? Agar WhatsApp same webhook 2 dafa bhej de (ye hota hai!), to customer ko 2 jawab na jaayein — iska kya hal hai? (hint: har message ki apni unique id hoti hai)

---

## ❌ Ye endpoints galat kyun hain? Theek karke likho

1. `GET /getProductById?id=5` →
2. `POST /orders/create` →
3. `GET /deleteOrder/5` →
4. `POST /product` →
5. `GET /orders/5/customer/7/products/3/reviews` →
