"""Leapexbiz TCSP admin backend API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional

from ..db import get_session
from .. import models as M

router = APIRouter(prefix="/api/tcsp", tags=["tcsp"])


def _all(s, cls, order=None):
    q = select(cls)
    rows = s.exec(q).all()
    return [r.model_dump() for r in rows]


# ── Dashboard ──
@router.get("/dashboard")
def dashboard(s: Session = Depends(get_session)):
    kyc_pending = len([k for k in s.exec(select(M.TcspKyc)).all()
                       if k.status in ("submitted", "reviewing")])
    nc_pending = len([n for n in s.exec(select(M.TcspNameCheck)).all() if n.status == "pending"])
    bills_confirm = len([b for b in s.exec(select(M.TcspBill)).all() if b.status == "待确认"])
    revenue = sum(b.amount for b in s.exec(select(M.TcspBill)).all() if b.status == "已到账")
    comm_payable = sum(c.commission for c in s.exec(select(M.TcspCommission)).all()
                       if c.settle_status == "待结算")
    sup_payable = sum(sb.amount for sb in s.exec(select(M.TcspSupplierBill)).all()
                      if sb.settle_status == "待结算")
    return {
        "kyc_pending": kyc_pending, "nc_pending": nc_pending, "bills_confirm": bills_confirm,
        "revenue_recognized": revenue, "commission_payable": comm_payable,
        "supplier_payable": sup_payable,
        "new_orders_today": len(s.exec(select(M.TcspOrder)).all()),
    }


# ── Resource listings ──
@router.get("/customers")
def customers(s: Session = Depends(get_session)):
    return _all(s, M.TcspCustomer)


@router.get("/kyc")
def kyc(status: Optional[str] = None, s: Session = Depends(get_session)):
    rows = s.exec(select(M.TcspKyc)).all()
    if status:
        rows = [r for r in rows if r.status == status]
    return [r.model_dump() for r in rows]


@router.post("/kyc/{kid}/{action}")
def kyc_action(kid: str, action: str, s: Session = Depends(get_session)):
    k = s.get(M.TcspKyc, kid)
    if not k:
        raise HTTPException(404, "not found")
    mp = {"approve": "approved", "reject": "rejected", "edd": "edd_required",
          "request-more": "reviewing"}
    if action not in mp:
        raise HTTPException(400, "bad action")
    k.status = mp[action]
    s.add(k); s.commit()
    # propagate to customer
    c = s.get(M.TcspCustomer, k.customer_id)
    if c:
        c.kyc_status = {"approved": "approved", "rejected": "rejected",
                        "edd_required": "edd", "reviewing": "reviewing"}[k.status]
        s.add(c); s.commit()
    return {"ok": True, "status": k.status}


@router.get("/namechecks")
def namechecks(s: Session = Depends(get_session)):
    return _all(s, M.TcspNameCheck)


@router.get("/orders")
def orders(s: Session = Depends(get_session)):
    return _all(s, M.TcspOrder)


@router.get("/bills")
def bills(status: Optional[str] = None, s: Session = Depends(get_session)):
    rows = s.exec(select(M.TcspBill)).all()
    if status:
        rows = [r for r in rows if r.status == status]
    return [r.model_dump() for r in rows]


@router.post("/bills/{bid}/confirm")
def bill_confirm(bid: str, s: Session = Depends(get_session)):
    b = s.get(M.TcspBill, bid)
    if not b:
        raise HTTPException(404, "not found")
    b.status = "已到账"
    s.add(b); s.commit()
    # order → 服务中
    o = s.get(M.TcspOrder, b.order_id)
    if o and o.status == "待支付":
        o.status = "服务中"; s.add(o); s.commit()
    return {"ok": True}


@router.post("/bills/{bid}/reject")
def bill_reject(bid: str, s: Session = Depends(get_session)):
    b = s.get(M.TcspBill, bid)
    if not b:
        raise HTTPException(404, "not found")
    b.status = "已驳回"; s.add(b); s.commit()
    return {"ok": True}


@router.get("/channels")
def channels(s: Session = Depends(get_session)):
    return _all(s, M.TcspChannel)


@router.get("/commissions")
def commissions(s: Session = Depends(get_session)):
    return _all(s, M.TcspCommission)


@router.post("/commissions/{cid}/settle")
def settle_commission(cid: int, s: Session = Depends(get_session)):
    c = s.get(M.TcspCommission, cid)
    if not c:
        raise HTTPException(404, "not found")
    c.settle_status = "已结算"; s.add(c); s.commit()
    return {"ok": True}


@router.get("/suppliers")
def suppliers(s: Session = Depends(get_session)):
    return _all(s, M.TcspSupplier)


@router.get("/supplier-bills")
def supplier_bills(s: Session = Depends(get_session)):
    return _all(s, M.TcspSupplierBill)


@router.post("/supplier-bills/{sid}/settle")
def settle_supplier(sid: str, s: Session = Depends(get_session)):
    sb = s.get(M.TcspSupplierBill, sid)
    if not sb:
        raise HTTPException(404, "not found")
    sb.settle_status = "已结算"; s.add(sb); s.commit()
    return {"ok": True}


@router.get("/leads")
def leads(s: Session = Depends(get_session)):
    return _all(s, M.TcspLead)
