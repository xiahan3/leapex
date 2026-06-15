"""SQLModel ORM models for EasybookX MVP.

Design notes:
- Single-tenant for MVP (no tenant/company FK enforcement; company_id is a free-form string).
- 'extra' JSON column on each table holds flexible fields from the prototype that
  we do not yet model explicitly. This avoids schema churn while we iterate.
"""
from datetime import datetime
from typing import Optional, List, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text


# ─── COA ─────────────────────────────────────────────────────────────
class COA(SQLModel, table=True):
    __tablename__ = "coa"
    code: str = Field(primary_key=True)
    en: str
    zh: str
    level: int
    parent_code: Optional[str] = None
    category: str  # A/L/E/I/X
    normal_balance: str  # Dr/Cr
    postable: bool = True
    active: bool = True
    sort_order: int = 0


# ─── Bank Statement ──────────────────────────────────────────────────
class BankStatement(SQLModel, table=True):
    __tablename__ = "bank_statement"
    id: str = Field(primary_key=True)
    company_id: str = Field(default="ABC", index=True)
    filename: str
    bank: str
    bank_color: Optional[str] = None
    acct_no: str
    acct_type: str
    period: str = Field(index=True)  # YYYY-MM
    txn_count: int = 0
    end_balance: Optional[str] = None
    month_label: Optional[str] = None
    status: str = "done"  # uploading/parsing/done/failed
    stage: str = "parsed"  # parsed / staged
    is_own: bool = True
    company: Optional[str] = None
    note: Optional[str] = None
    pages: Optional[int] = None
    total_pages: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Invoice ─────────────────────────────────────────────────────────
class Invoice(SQLModel, table=True):
    __tablename__ = "invoice"
    id: str = Field(primary_key=True)
    company_id: str = Field(default="ABC", index=True)
    stage: str = "parsed"  # parsed / staged
    period: Optional[str] = Field(default=None, index=True)
    filename: Optional[str] = None
    merchant: Optional[str] = None
    invoice_no: Optional[str] = None
    category: Optional[str] = None
    invoice_date: Optional[str] = None
    amt: Optional[str] = None
    currency: str = "HKD"
    invoice_type: str = "expense"  # income/expense/unknown
    ai_confidence: int = 0
    parse_status: str = "done"
    is_own: bool = True
    is_duplicate: bool = False
    recon_state: str = "unmatched"
    s3_key: Optional[str] = None
    upload_err: Optional[str] = None
    note: Optional[str] = None
    my_company: Optional[str] = None
    counterparty: Optional[str] = None
    upload_at: Optional[str] = None
    upload_st: str = "done"
    extra: Optional[dict] = Field(default=None, sa_column=Column(JSON))


# ─── Recon Pair ──────────────────────────────────────────────────────
class ReconPair(SQLModel, table=True):
    __tablename__ = "recon_pair"
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: str = Field(default="ABC", index=True)
    period: str = Field(index=True)
    pair_index: int  # original position in array
    status: str  # match/annotated/pending/unmatched/orphan
    txn: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    invs: List[Any] = Field(default_factory=list, sa_column=Column(JSON))
    pay_method: Optional[str] = None
    unmatched_note: Optional[str] = None


# ─── Journal Entry & Lines ───────────────────────────────────────────
class JournalEntry(SQLModel, table=True):
    __tablename__ = "journal_entry"
    id: str = Field(primary_key=True)  # JV-YYYY-NNN
    company_id: str = Field(default="ABC", index=True)
    entry_date: str
    description: str
    status: str = "pending"
    source: str = "manual"
    source_ref: Optional[str] = None
    ai_confidence: Optional[int] = None
    lines: List[Any] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Cash Entry ──────────────────────────────────────────────────────
class CashEntry(SQLModel, table=True):
    __tablename__ = "cash_entry"
    id: str = Field(primary_key=True)
    company_id: str = Field(default="ABC", index=True)
    date: str
    desc: str
    entry_type: str  # expense/income
    dr_code: str
    cr_code: str
    currency: str = "HKD"
    amt: float
    voucher: Optional[str] = None
    recon_st: str = "orphan"
    payer: Optional[str] = None
    notes: Optional[str] = None


# ─── Adjustment Entry ────────────────────────────────────────────────
class AdjEntry(SQLModel, table=True):
    __tablename__ = "adj_entry"
    id: str = Field(primary_key=True)  # ADJ-NNN
    company_id: str = Field(default="ABC", index=True)
    period: str = Field(default="2026-01", index=True)
    cat: str  # dep/accrued/prepaid/revenue/tax/other
    dr_acct: str
    cr_acct: str
    amt: float
    desc: str
    status: str = "pending"


# ─── Company Profile / Init ──────────────────────────────────────────
class CompanyProfile(SQLModel, table=True):
    __tablename__ = "company_profile"
    company_id: str = Field(primary_key=True)
    name: str
    br_no: Optional[str] = None
    fy_start_month: int = 7
    first_period: Optional[str] = None
    base_currency: str = "HKD"
    closing_freq: str = "quarterly"
    is_first_year: bool = False
    fy_start: Optional[str] = None
    fy_end: Optional[str] = None
    opening_tb: Optional[dict] = Field(default=None, sa_column=Column(JSON))
