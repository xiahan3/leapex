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


# ═══════════════════════════════════════════════════════════════════
#  平台管理 (Platform Management) — 超级管理员 / 多租户 SaaS 运营
# ═══════════════════════════════════════════════════════════════════

# ─── Tenant 租户 ─────────────────────────────────────────────────────
class Tenant(SQLModel, table=True):
    __tablename__ = "tenant"
    id: str = Field(primary_key=True)              # T-2026-NNNN
    name: str
    type: str = "CPA Firm"                          # CPA Firm / 独立 SME / 企业集团 / 个人
    plan: str = "Professional"
    companies: int = 0
    users: int = 1
    token_used: int = 0
    token_quota: int = 200000
    mrr: float = 0
    status: str = "trial"                           # active / trial / suspended
    status_pill: str = "p-blue"
    br_no: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None
    expire_at: Optional[str] = None


# ─── Tenant User 平台员工账号 ────────────────────────────────────────
class TenantUser(SQLModel, table=True):
    __tablename__ = "tenant_user"
    id: str = Field(primary_key=True)              # U-2026-NNNNN
    tenant_id: str = Field(default="T-2026-0001", index=True)
    name: str
    email: str
    phone: Optional[str] = None
    role: str = "bookkeeper"                        # tenant_admin/senior/bookkeeper/reviewer/viewer
    companies: int = 0
    last: Optional[str] = None
    status: str = "active"                          # active / invited / disabled
    twofa: bool = False
    is_self: bool = False


# ─── Plan 套餐 ───────────────────────────────────────────────────────
class Plan(SQLModel, table=True):
    __tablename__ = "plan"
    key: str = Field(primary_key=True)
    name: str
    price: Optional[float] = None                  # None = 商谈
    unit: str = "/ 月"
    max_companies: str = "0"                        # str 以容纳 "不限"
    max_users: str = "0"
    token_quota: str = "0"                          # str 以容纳 "按需"
    features: List[Any] = Field(default_factory=list, sa_column=Column(JSON))
    rec: bool = False
    sort_order: int = 0


# ─── Billing Invoice 平台账单 (区别于会计 Invoice) ───────────────────
class BillingInvoice(SQLModel, table=True):
    __tablename__ = "billing_invoice"
    no: str = Field(primary_key=True)              # INV-YYYY-MM-TNNNN
    tenant: str
    plan: Optional[str] = None
    total: float = 0
    subtotal: float = 0
    discount: float = 0
    method: Optional[str] = "—"
    channel: str = "offline"                        # online / offline
    status: str = "issued"                          # draft/issued/proof_uploaded/paid/overdue/rejected/receipted
    period: Optional[str] = None
    items: List[Any] = Field(default_factory=list, sa_column=Column(JSON))


# ─── Audit Report 审计报告记录 ───────────────────────────────────────
class AuditReport(SQLModel, table=True):
    __tablename__ = "audit_report"
    no: str = Field(primary_key=True)              # AR-YYYY-NNNN
    company_id: Optional[str] = None
    company: str
    period: Optional[str] = None
    report_type: str = "审前分析报告"
    framework: str = "SME-FRS"
    score: int = 0
    payload: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


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


# ═══════════════════════ Leapexbiz TCSP 业务域 ═══════════════════════
class TcspCustomer(SQLModel, table=True):
    __tablename__ = "tcsp_customer"
    id: str = Field(primary_key=True)
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    channel_code: Optional[str] = None
    source: str = "organic"            # channel / organic
    kyc_status: str = "none"           # none/submitted/reviewing/approved/edd/rejected/frozen
    tags: List[Any] = Field(default_factory=list, sa_column=Column(JSON))
    company_count: int = 0
    order_count: int = 0
    created_at: str = ""


class TcspKyc(SQLModel, table=True):
    __tablename__ = "tcsp_kyc"
    id: str = Field(primary_key=True)
    customer_id: str = Field(index=True)
    customer_name: str = ""
    id_doc_type: str = "hkid"
    is_pep: bool = False
    pep_relations: Optional[str] = None
    sanction_hit: bool = False
    status: str = "submitted"          # submitted/reviewing/approved/edd_required/rejected/frozen
    reject_reason: Optional[str] = None
    submitted_at: str = ""
    sla_hours: int = 48


class TcspNameCheck(SQLModel, table=True):
    __tablename__ = "tcsp_namecheck"
    id: str = Field(primary_key=True)
    customer_id: str = ""
    name_en: str = ""
    name_zh: str = ""
    precheck: str = "pending"
    icris: str = "pending"             # pending/done/blocked
    risk_level: Optional[str] = None   # G/Y/O/R/B
    recheck_count: int = 0
    free_quota: int = 3
    status: str = "pending"            # pending/done/locked


class TcspOrder(SQLModel, table=True):
    __tablename__ = "tcsp_order"
    id: str = Field(primary_key=True)  # ORD-...
    customer_id: str = ""
    customer_name: str = ""
    service: str = ""
    channel_code: Optional[str] = None
    amount: float = 0
    status: str = "待支付"             # 待支付/服务中/已完成/已取消
    created_at: str = ""


class TcspBill(SQLModel, table=True):
    __tablename__ = "tcsp_bill"
    id: str = Field(primary_key=True)  # LEA-...
    order_id: str = ""
    customer_name: str = ""
    service_item: str = ""
    amount: float = 0
    stamp_duty: float = 0
    proof_uploaded: bool = False
    status: str = "待支付"             # 待支付/待确认/已到账/已驳回/已作废
    reopen_count: int = 0


class TcspChannel(SQLModel, table=True):
    __tablename__ = "tcsp_channel"
    code: str = Field(primary_key=True)
    partner_name: str = ""
    orders_month: int = 0
    revenue_month: float = 0
    commission_month: float = 0
    settle_status: str = "待结算"


class TcspCommission(SQLModel, table=True):
    __tablename__ = "tcsp_commission"
    id: Optional[int] = Field(default=None, primary_key=True)
    channel_code: str = ""
    order_id: str = ""
    service: str = ""
    base_amount: float = 0
    rate: float = 0
    commission: float = 0
    period: str = ""
    settle_status: str = "待结算"


class TcspSupplier(SQLModel, table=True):
    __tablename__ = "tcsp_supplier"
    id: str = Field(primary_key=True)
    name: str = ""
    service_types: str = ""
    active_tasks: int = 0
    payable_month: float = 0
    status: str = "active"


class TcspSupplierBill(SQLModel, table=True):
    __tablename__ = "tcsp_supplier_bill"
    id: str = Field(primary_key=True)  # SUP-...
    supplier_name: str = ""
    service_desc: str = ""
    amount: float = 0
    period: str = ""
    settle_status: str = "待结算"


class TcspLead(SQLModel, table=True):
    __tablename__ = "tcsp_lead"
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_name: str = ""
    source: str = ""                   # svc_detail/order_confirm/fab/partner
    intent_service: str = ""
    status: str = "待跟进"             # 待跟进/跟进中/已转化/关闭
    owner: Optional[str] = None
    created_at: str = ""
