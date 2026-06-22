"""EasybookX MVP backend — FastAPI app."""
import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any

from .db import engine, init_db, get_session
from . import models as M

app = FastAPI(title="EasybookX API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
def on_startup():
    init_db()
    # auto-seed if empty
    from . import seed
    with Session(engine) as s:
        n = s.exec(select(M.COA)).first()
        if not n:
            seed.run(s)


# ═══════════ Health ═══════════
@app.get("/api/health")
def health():
    return {"ok": True, "service": "easybookx", "version": "1.0.0"}


# ═══════════ Helpers ═══════════
def row_to_dict(row) -> Dict[str, Any]:
    if hasattr(row, "model_dump"):
        return row.model_dump()
    return dict(row)


def upsert(session: Session, model_cls, pk_field: str, data: dict):
    pk = data.get(pk_field)
    existing = session.get(model_cls, pk) if pk else None
    if existing:
        for k, v in data.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    obj = model_cls(**{k: v for k, v in data.items() if hasattr(model_cls, k)})
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


# ═══════════ COA ═══════════
@app.get("/api/coa")
def list_coa(session: Session = Depends(get_session)):
    rows = session.exec(select(M.COA).order_by(M.COA.code)).all()
    return [r.model_dump() for r in rows]


@app.post("/api/coa")
def upsert_coa(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.COA, "code", payload).model_dump()


@app.patch("/api/coa/{code}")
def patch_coa(code: str, payload: dict, session: Session = Depends(get_session)):
    payload["code"] = code
    return upsert(session, M.COA, "code", payload).model_dump()


@app.delete("/api/coa/{code}")
def delete_coa(code: str, session: Session = Depends(get_session)):
    row = session.get(M.COA, code)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ═══════════ Bank Statements ═══════════
@app.get("/api/bank-statements")
def list_bank(period: Optional[str] = None, stage: Optional[str] = None,
              session: Session = Depends(get_session)):
    q = select(M.BankStatement)
    if period:
        q = q.where(M.BankStatement.period == period)
    if stage:
        q = q.where(M.BankStatement.stage == stage)
    return [r.model_dump() for r in session.exec(q).all()]


@app.post("/api/bank-statements")
def upsert_bank(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.BankStatement, "id", payload).model_dump()


@app.patch("/api/bank-statements/{bid}")
def patch_bank(bid: str, payload: dict, session: Session = Depends(get_session)):
    payload["id"] = bid
    return upsert(session, M.BankStatement, "id", payload).model_dump()


@app.delete("/api/bank-statements/{bid}")
def del_bank(bid: str, session: Session = Depends(get_session)):
    row = session.get(M.BankStatement, bid)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ═══════════ Invoices ═══════════
@app.get("/api/invoices")
def list_invoices(stage: Optional[str] = None, period: Optional[str] = None,
                  invoice_type: Optional[str] = None,
                  session: Session = Depends(get_session)):
    q = select(M.Invoice)
    if stage:
        q = q.where(M.Invoice.stage == stage)
    if period:
        q = q.where(M.Invoice.period == period)
    if invoice_type:
        q = q.where(M.Invoice.invoice_type == invoice_type)
    return [r.model_dump() for r in session.exec(q).all()]


@app.post("/api/invoices")
def upsert_invoice(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.Invoice, "id", payload).model_dump()


@app.patch("/api/invoices/{iid}")
def patch_invoice(iid: str, payload: dict, session: Session = Depends(get_session)):
    payload["id"] = iid
    return upsert(session, M.Invoice, "id", payload).model_dump()


@app.delete("/api/invoices/{iid}")
def del_invoice(iid: str, session: Session = Depends(get_session)):
    row = session.get(M.Invoice, iid)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ═══════════ Recon Pairs ═══════════
@app.get("/api/recon-pairs")
def list_recon(period: str, session: Session = Depends(get_session)):
    q = select(M.ReconPair).where(M.ReconPair.period == period).order_by(M.ReconPair.pair_index)
    return [r.model_dump() for r in session.exec(q).all()]


@app.post("/api/recon-pairs/bulk")
def bulk_recon(payload: dict, session: Session = Depends(get_session)):
    """Replace all pairs for a period with provided list."""
    period = payload["period"]
    pairs = payload.get("pairs", [])
    existing = session.exec(select(M.ReconPair).where(M.ReconPair.period == period)).all()
    for r in existing:
        session.delete(r)
    session.commit()
    for i, p in enumerate(pairs):
        row = M.ReconPair(
            period=period, pair_index=i,
            status=p.get("st", "unmatched"),
            txn=p.get("txn"),
            invs=p.get("invs", []),
            pay_method=p.get("payMethod"),
            unmatched_note=p.get("unmatchedNote"),
        )
        session.add(row)
    session.commit()
    return {"ok": True, "count": len(pairs)}


@app.patch("/api/recon-pairs/{pid}")
def patch_recon(pid: int, payload: dict, session: Session = Depends(get_session)):
    row = session.get(M.ReconPair, pid)
    if not row:
        raise HTTPException(404, "not found")
    for k, v in payload.items():
        if k == "st":
            row.status = v
        elif hasattr(row, k):
            setattr(row, k, v)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row.model_dump()


# ═══════════ Journal Entries ═══════════
@app.get("/api/journals")
def list_journals(status: Optional[str] = None, period: Optional[str] = None,
                  session: Session = Depends(get_session)):
    q = select(M.JournalEntry)
    if status:
        q = q.where(M.JournalEntry.status == status)
    rows = session.exec(q).all()
    if period:
        # period filter on date prefix
        rows = [r for r in rows if (r.entry_date or "").startswith(period)]
    return [r.model_dump() for r in rows]


@app.post("/api/journals")
def upsert_journal(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.JournalEntry, "id", payload).model_dump()


@app.patch("/api/journals/{jid}")
def patch_journal(jid: str, payload: dict, session: Session = Depends(get_session)):
    payload["id"] = jid
    return upsert(session, M.JournalEntry, "id", payload).model_dump()


@app.post("/api/journals/{jid}/confirm")
def confirm_journal(jid: str, session: Session = Depends(get_session)):
    row = session.get(M.JournalEntry, jid)
    if not row:
        raise HTTPException(404, "not found")
    row.status = "confirmed"
    session.add(row)
    session.commit()
    return {"ok": True}


@app.delete("/api/journals/{jid}")
def del_journal(jid: str, session: Session = Depends(get_session)):
    row = session.get(M.JournalEntry, jid)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ═══════════ Cash Entries ═══════════
@app.get("/api/cash-entries")
def list_cash(session: Session = Depends(get_session)):
    return [r.model_dump() for r in session.exec(select(M.CashEntry)).all()]


@app.post("/api/cash-entries")
def upsert_cash(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.CashEntry, "id", payload).model_dump()


@app.patch("/api/cash-entries/{cid}")
def patch_cash(cid: str, payload: dict, session: Session = Depends(get_session)):
    payload["id"] = cid
    return upsert(session, M.CashEntry, "id", payload).model_dump()


@app.delete("/api/cash-entries/{cid}")
def del_cash(cid: str, session: Session = Depends(get_session)):
    row = session.get(M.CashEntry, cid)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ═══════════ Adjustment Entries ═══════════
@app.get("/api/adj-entries")
def list_adj(period: Optional[str] = None, session: Session = Depends(get_session)):
    q = select(M.AdjEntry)
    if period:
        q = q.where(M.AdjEntry.period == period)
    return [r.model_dump() for r in session.exec(q).all()]


@app.post("/api/adj-entries")
def upsert_adj(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.AdjEntry, "id", payload).model_dump()


@app.patch("/api/adj-entries/{aid}")
def patch_adj(aid: str, payload: dict, session: Session = Depends(get_session)):
    payload["id"] = aid
    return upsert(session, M.AdjEntry, "id", payload).model_dump()


@app.post("/api/adj-entries/confirm-all")
def confirm_all_adj(period: Optional[str] = None, session: Session = Depends(get_session)):
    q = select(M.AdjEntry)
    if period:
        q = q.where(M.AdjEntry.period == period)
    for row in session.exec(q).all():
        row.status = "confirmed"
        session.add(row)
    session.commit()
    return {"ok": True}


@app.delete("/api/adj-entries/{aid}")
def del_adj(aid: str, session: Session = Depends(get_session)):
    row = session.get(M.AdjEntry, aid)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ═══════════ Trial Balance & Reports ═══════════
@app.get("/api/trial-balance")
def trial_balance(period: Optional[str] = None, session: Session = Depends(get_session)):
    """Aggregate all confirmed JE lines per account_code → dr/cr totals."""
    je_rows = session.exec(
        select(M.JournalEntry).where(M.JournalEntry.status == "confirmed")
    ).all()
    if period:
        je_rows = [r for r in je_rows if (r.entry_date or "").startswith(period)]
    # adj entries (confirmed) — they don't have line structure; we treat dr_acct/cr_acct as one line each
    adj_rows = session.exec(
        select(M.AdjEntry).where(M.AdjEntry.status == "confirmed")
    ).all()
    if period:
        adj_rows = [r for r in adj_rows if r.period == period]

    agg: Dict[str, Dict[str, float]] = {}
    coa_index = {c.en: c for c in session.exec(select(M.COA)).all()}

    def add(account_key: str, dr: float, cr: float):
        d = agg.setdefault(account_key, {"dr": 0.0, "cr": 0.0})
        d["dr"] += dr
        d["cr"] += cr

    for je in je_rows:
        for line in (je.lines or []):
            acct = line.get("account") or ""
            amt = float(line.get("amount") or 0)
            if line.get("type") == "Dr":
                add(acct, amt, 0)
            else:
                add(acct, 0, amt)

    for adj in adj_rows:
        add(adj.dr_acct, adj.amt, 0)
        add(adj.cr_acct, 0, adj.amt)

    rows = []
    dr_total = 0.0
    cr_total = 0.0
    for name, v in sorted(agg.items()):
        coa_hit = coa_index.get(name.split(" (")[0])
        rows.append({
            "account": name,
            "code": coa_hit.code if coa_hit else None,
            "category": coa_hit.category if coa_hit else None,
            "dr": round(v["dr"], 2),
            "cr": round(v["cr"], 2),
        })
        dr_total += v["dr"]
        cr_total += v["cr"]
    diff = round(dr_total - cr_total, 2)
    return {
        "period": period,
        "rows": rows,
        "dr_total": round(dr_total, 2),
        "cr_total": round(cr_total, 2),
        "balanced": abs(diff) < 0.01,
        "diff": diff,
    }


@app.get("/api/reports/pl")
def report_pl(period: Optional[str] = None, session: Session = Depends(get_session)):
    tb = trial_balance(period, session)
    revenue = sum(r["cr"] - r["dr"] for r in tb["rows"] if r["category"] == "I")
    expenses = sum(r["dr"] - r["cr"] for r in tb["rows"] if r["category"] == "X")
    return {
        "period": period,
        "revenue": round(revenue, 2),
        "expenses": round(expenses, 2),
        "net_profit": round(revenue - expenses, 2),
        "lines": tb["rows"],
    }


@app.get("/api/reports/bs")
def report_bs(period: Optional[str] = None, session: Session = Depends(get_session)):
    tb = trial_balance(period, session)
    assets = sum(r["dr"] - r["cr"] for r in tb["rows"] if r["category"] == "A")
    liabilities = sum(r["cr"] - r["dr"] for r in tb["rows"] if r["category"] == "L")
    equity = sum(r["cr"] - r["dr"] for r in tb["rows"] if r["category"] == "E")
    return {
        "period": period,
        "assets": round(assets, 2),
        "liabilities": round(liabilities, 2),
        "equity": round(equity, 2),
        "balanced": abs(round(assets - liabilities - equity, 2)) < 0.01,
        "lines": tb["rows"],
    }


# ═══════════ Company Profile ═══════════
@app.get("/api/company")
def get_company(cid: str = "ABC", session: Session = Depends(get_session)):
    row = session.get(M.CompanyProfile, cid)
    return row.model_dump() if row else {"company_id": cid, "name": "ABC Trading Co. Ltd"}


@app.post("/api/company")
def save_company(payload: dict, session: Session = Depends(get_session)):
    payload.setdefault("company_id", "ABC")
    return upsert(session, M.CompanyProfile, "company_id", payload).model_dump()


# ═══════════════════════════════════════════════════════════════════
#  平台管理 (Platform Management) APIs
# ═══════════════════════════════════════════════════════════════════

# ─── Tenants ───────────────────────────────────────────────────────
@app.get("/api/tenants")
def list_tenants(status: Optional[str] = None, session: Session = Depends(get_session)):
    q = select(M.Tenant)
    if status:
        q = q.where(M.Tenant.status == status)
    return [r.model_dump() for r in session.exec(q).all()]


@app.post("/api/tenants")
def upsert_tenant(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.Tenant, "id", payload).model_dump()


@app.patch("/api/tenants/{tid}")
def patch_tenant(tid: str, payload: dict, session: Session = Depends(get_session)):
    payload["id"] = tid
    return upsert(session, M.Tenant, "id", payload).model_dump()


@app.delete("/api/tenants/{tid}")
def del_tenant(tid: str, session: Session = Depends(get_session)):
    row = session.get(M.Tenant, tid)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ─── Tenant Users ──────────────────────────────────────────────────
@app.get("/api/tenant-users")
def list_tenant_users(tenant_id: Optional[str] = None, role: Optional[str] = None,
                      status: Optional[str] = None, session: Session = Depends(get_session)):
    q = select(M.TenantUser)
    if tenant_id:
        q = q.where(M.TenantUser.tenant_id == tenant_id)
    if role:
        q = q.where(M.TenantUser.role == role)
    if status:
        q = q.where(M.TenantUser.status == status)
    return [r.model_dump() for r in session.exec(q).all()]


@app.post("/api/tenant-users")
def upsert_tenant_user(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.TenantUser, "id", payload).model_dump()


@app.patch("/api/tenant-users/{uid}")
def patch_tenant_user(uid: str, payload: dict, session: Session = Depends(get_session)):
    payload["id"] = uid
    return upsert(session, M.TenantUser, "id", payload).model_dump()


@app.delete("/api/tenant-users/{uid}")
def del_tenant_user(uid: str, session: Session = Depends(get_session)):
    row = session.get(M.TenantUser, uid)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ─── Plans ─────────────────────────────────────────────────────────
@app.get("/api/plans")
def list_plans(session: Session = Depends(get_session)):
    rows = session.exec(select(M.Plan).order_by(M.Plan.sort_order)).all()
    return [r.model_dump() for r in rows]


@app.post("/api/plans")
def upsert_plan(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.Plan, "key", payload).model_dump()


@app.patch("/api/plans/{key}")
def patch_plan(key: str, payload: dict, session: Session = Depends(get_session)):
    payload["key"] = key
    return upsert(session, M.Plan, "key", payload).model_dump()


@app.delete("/api/plans/{key}")
def del_plan(key: str, session: Session = Depends(get_session)):
    row = session.get(M.Plan, key)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ─── Billing Invoices ──────────────────────────────────────────────
@app.get("/api/billing-invoices")
def list_billing(status: Optional[str] = None, period: Optional[str] = None,
                 session: Session = Depends(get_session)):
    q = select(M.BillingInvoice)
    if status:
        q = q.where(M.BillingInvoice.status == status)
    if period:
        q = q.where(M.BillingInvoice.period == period)
    return [r.model_dump() for r in session.exec(q).all()]


@app.post("/api/billing-invoices")
def upsert_billing(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.BillingInvoice, "no", payload).model_dump()


@app.patch("/api/billing-invoices/{no}")
def patch_billing(no: str, payload: dict, session: Session = Depends(get_session)):
    payload["no"] = no
    return upsert(session, M.BillingInvoice, "no", payload).model_dump()


@app.delete("/api/billing-invoices/{no}")
def del_billing(no: str, session: Session = Depends(get_session)):
    row = session.get(M.BillingInvoice, no)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ─── Audit Reports ─────────────────────────────────────────────────
@app.get("/api/audit-reports")
def list_audit_reports(company_id: Optional[str] = None, session: Session = Depends(get_session)):
    q = select(M.AuditReport).order_by(M.AuditReport.created_at.desc())
    if company_id:
        q = q.where(M.AuditReport.company_id == company_id)
    return [r.model_dump() for r in session.exec(q).all()]


@app.post("/api/audit-reports")
def create_audit_report(payload: dict, session: Session = Depends(get_session)):
    return upsert(session, M.AuditReport, "no", payload).model_dump()


@app.delete("/api/audit-reports/{no}")
def del_audit_report(no: str, session: Session = Depends(get_session)):
    row = session.get(M.AuditReport, no)
    if not row:
        raise HTTPException(404, "not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# ═══════════ Static frontend (HTML) ═══════════
@app.get("/")
def root():
    idx = STATIC_DIR / "index.html"
    if idx.exists():
        return FileResponse(idx)
    return JSONResponse({"msg": "easybookx backend up. UI not yet uploaded."})


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
