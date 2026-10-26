# PART A: HTTP Basics

**HTTP (HyperText Transfer Protocol)** = qawaid ka set jis se do computers (client aur server) internet par baat karte hain. Har baat ek **request** aur ek **response** hoti hai.

- **Client:** request bhejne wala (browser, mobile app, aap ka Python script, aap ka bot)
- **Server:** request lene aur jawab dene wala (FastAPI app, Shopify, OpenAI)
- **API:** server ke "darwaze" (endpoints) jin par program request bhej sakte hain

**HTTP stateless hai:** har request **akeli** hoti hai, server pichli request ko khud yaad nahi rakhta. Is liye har request ke saath API key/token/cookie bhejni parti hai.

## A.1 URL ke hisse

```
https://api.store.com:443/v1/orders/1042?include=items&limit=5#top
└─┬─┘   └─────┬─────┘└┬┘└──────┬──────┘└─────────┬────────┘└┬┘
scheme       host   port      path           query string  fragment
```

| Hissa | Matlab |
|---|---|
| **scheme** | `http` ya `https` (encrypted) |
| **host** | Server ka naam (DNS isay IP address mein badalta hai) |
| **port** | Server par darwaza number. HTTPS ka default 443, HTTP ka 80, aur hamara local server 8765 |
| **path** | Kaunsa resource: `/v1/orders/1042` |
| **query** | `?` ke baad `key=value` filters, `&` se jure |
| **fragment** | `#` wala hissa sirf browser ke liye hai. **Server tak jaata hi nahi** |

▶ Practice: `python -m part_a_http_basics.a1_url_parts`

## A.2 Request/Response cycle

**Request** ke 4 hisse: **method**, **URL**, **headers**, **body** (optional)
**Response** ke 3 hisse: **status code**, **headers**, **body**

```
GET /products/1 HTTP/1.1          ← method + path
Host: 127.0.0.1:8765              ← headers
Accept: */*

HTTP/1.1 200 OK                   ← status
content-type: application/json    ← headers

{"id":1,"name":"Classic Watch"}   ← body
```

▶ Practice (server chalna chahiye): `python -m part_a_http_basics.a2_request_response`

## A.3 🎤 Interview classic: "Browser mein URL likh kar Enter dabane par kya hota hai?"

1. **URL parse:** browser scheme, host, path alag karta hai
2. **DNS lookup:** `api.store.com` ka **IP address** dhoonda jata hai (browser cache → OS cache → router → DNS server)
3. **TCP connection:** client aur server ke beech connection banta hai (3-way handshake: SYN → SYN-ACK → ACK)
4. **TLS handshake (HTTPS):** server certificate dikhata hai, browser verify karta hai, aur dono ek encryption key tay karte hain. Ab sab data encrypted hai
5. **HTTP request:** `GET /v1/orders/1042` + headers bheje jaate hain
6. **Server processing:** load balancer → app server (FastAPI) → database/cache → response tayyar
7. **HTTP response:** status code + headers + body wapas aata hai
8. **Rendering:** browser HTML/JSON dikhata hai, aur zaroorat ho to aur requests (CSS, images) bhejta hai
9. **Connection reuse:** **keep-alive** se connection agli requests ke liye khula rehta hai (is liye `httpx.Client` reuse karna tez hai)

**Bonus points:** HTTPS mein bhi host (domain) network par nazar aata hai, lekin path, headers aur body encrypted hote hain. HTTP/2 ek connection par kai requests ek saath chalata hai.
