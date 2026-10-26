"""
F.3 Error handling: ConnectError, TimeoutException, HTTPStatusError
===================================================================
    python -m part_f_httpx_client.f3_error_handling

Theory: part_f_httpx_client/NOTES.md (F.3)
"""
import httpx

from common import get_client

client = get_client()


def get_product(product_id: int) -> dict | None:
    try:
        r = client.get(f"/products/{product_id}", timeout=5)
        r.raise_for_status()                      # 4xx/5xx -> HTTPStatusError
        return r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"   Product {product_id} mojood nahi")
            return None
        raise                                     # baqi errors upar bhejo
    except httpx.TimeoutException:
        print("   Server slow hai")
        return None
    except httpx.ConnectError:
        print("   Server tak pohanch nahi sake")
        return None


print(get_product(1))
print(get_product(999))

# Port 9 par koi server nahi -> ConnectError
try:
    httpx.get("http://127.0.0.1:9", timeout=2)
except httpx.ConnectError as e:
    print("ConnectError:", type(e).__name__)

client.close()
