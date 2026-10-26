from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.deps import verify_api_key
from app.schemas import OrderList, OrderOut, OrderStatus
from app.services import orders as order_service

router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=OrderList)
def list_orders(status: OrderStatus | None = None,
                limit: Annotated[int, Query(ge=1, le=100)] = 10,
                offset: Annotated[int, Query(ge=0)] = 0):
    items, total = order_service.list_orders(status, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: Annotated[str, Path(pattern=r"^\d{4}$")]):
    order = order_service.get_order(order_id)
    if order is None:
        raise HTTPException(404, f"Order {order_id} nahi mila")
    return order
