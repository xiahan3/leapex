"""Seed for Leapexbiz TCSP domain (admin backend)."""
from sqlmodel import Session, select
from . import models as M


def run(s: Session):
    if s.exec(select(M.TcspCustomer)).first():
        return

    customers = [
        M.TcspCustomer(id="C001", name="陈大文", email="andy@abc.hk", phone="+852 9123 4567",
                       channel_code="AGT001", source="channel", kyc_status="approved",
                       tags=["高价值"], company_count=2, order_count=3, created_at="2026-05-12"),
        M.TcspCustomer(id="C002", name="李美琪", email="mary@xy.hk", channel_code=None,
                       source="organic", kyc_status="reviewing", company_count=1, order_count=1,
                       created_at="2026-06-08"),
        M.TcspCustomer(id="C003", name="王志强", email="wang@fortune.hk", channel_code="AGT002",
                       source="channel", kyc_status="edd", tags=["PEP"], company_count=1,
                       order_count=2, created_at="2026-06-01"),
        M.TcspCustomer(id="C004", name="张倩", email="zhang@peak.hk", source="organic",
                       kyc_status="rejected", company_count=0, order_count=1, created_at="2026-05-28"),
    ]
    for c in customers:
        s.add(c)

    kycs = [
        M.TcspKyc(id="KYC-001", customer_id="C002", customer_name="李美琪", id_doc_type="hkid",
                  status="submitted", submitted_at="2026-06-08 09:32"),
        M.TcspKyc(id="KYC-002", customer_id="C005", customer_name="刘建国", id_doc_type="cn_id",
                  is_pep=True, pep_relations="含家属", status="edd_required", submitted_at="2026-06-07 16:20"),
        M.TcspKyc(id="KYC-003", customer_id="C006", customer_name="Ahmed K.", id_doc_type="passport",
                  sanction_hit=True, status="frozen", submitted_at="2026-06-08 11:05"),
        M.TcspKyc(id="KYC-004", customer_id="C007", customer_name="周敏", id_doc_type="hkid",
                  status="submitted", submitted_at="2026-06-08 13:40"),
    ]
    for k in kycs:
        s.add(k)

    ncs = [
        M.TcspNameCheck(id="NC-001", customer_id="C001", name_en="Star Tech Limited", name_zh="星辰科技有限公司",
                        precheck="done", icris="pending", recheck_count=0, status="pending"),
        M.TcspNameCheck(id="NC-002", customer_id="C002", name_en="Global Vision Limited", name_zh="环球视野有限公司",
                        precheck="similar", icris="pending", recheck_count=1, status="pending"),
        M.TcspNameCheck(id="NC-003", customer_id="C003", name_en="Royal Trust Limited", name_zh="皇家信托有限公司",
                        precheck="sensitive", icris="blocked", risk_level="B", recheck_count=2, status="pending"),
    ]
    for n in ncs:
        s.add(n)

    orders = [
        M.TcspOrder(id="ORD-2026-0188", customer_id="C001", customer_name="陈大文", service="标准注册套餐",
                    channel_code="AGT001", amount=5500, status="服务中", created_at="2026-06-05"),
        M.TcspOrder(id="ORD-2026-0205", customer_id="C002", customer_name="李美琪", service="年审服务",
                    channel_code=None, amount=2800, status="待支付", created_at="2026-06-08"),
        M.TcspOrder(id="ORD-2026-0142", customer_id="C001", customer_name="恒丰贸易", service="年审 + 董事变更",
                    channel_code="AGT001", amount=2300, status="已完成", created_at="2026-05-20"),
    ]
    for o in orders:
        s.add(o)

    bills = [
        M.TcspBill(id="LEA-2026-0188-1", order_id="ORD-2026-0188", customer_name="陈大文",
                   service_item="标准注册（首付）", amount=2750, proof_uploaded=True, status="待确认"),
        M.TcspBill(id="LEA-2026-0210-1", order_id="ORD-2026-0210", customer_name="科达",
                   service_item="股份转让", amount=2000, stamp_duty=1200, proof_uploaded=True, status="待确认"),
        M.TcspBill(id="LEA-2026-0205-1", order_id="ORD-2026-0205", customer_name="李美琪",
                   service_item="年审", amount=2800, proof_uploaded=False, status="待支付"),
        M.TcspBill(id="LEA-2026-0142-2", order_id="ORD-2026-0142", customer_name="恒丰",
                   service_item="董事变更", amount=800, status="已到账"),
    ]
    for b in bills:
        s.add(b)

    channels = [
        M.TcspChannel(code="AGT001", partner_name="星投资本", orders_month=18, revenue_month=96000,
                      commission_month=14200, settle_status="待结算"),
        M.TcspChannel(code="AGT002", partner_name="正弦咨询", orders_month=12, revenue_month=64000,
                      commission_month=11800, settle_status="待结算"),
        M.TcspChannel(code="AGT003", partner_name="湾区财税", orders_month=9, revenue_month=48000,
                      commission_month=8200, settle_status="已结算"),
    ]
    for ch in channels:
        s.add(ch)

    comms = [
        M.TcspCommission(channel_code="AGT001", order_id="ORD-2026-0188", service="公司注册（基础）",
                         base_amount=3500, rate=0.12, commission=420, period="2026-06", settle_status="待结算"),
        M.TcspCommission(channel_code="AGT002", order_id="ORD-2026-0191", service="年审",
                         base_amount=2400, rate=0.10, commission=240, period="2026-06", settle_status="待结算"),
        M.TcspCommission(channel_code="AGT003", order_id="ORD-2026-0177", service="董事变更",
                         base_amount=1500, rate=0.04, commission=60, period="2026-06", settle_status="已结算"),
    ]
    for cm in comms:
        s.add(cm)

    suppliers = [
        M.TcspSupplier(id="S001", name="金印堂", service_types="印章制作", active_tasks=3,
                       payable_month=4800, status="active"),
        M.TcspSupplier(id="S002", name="正诚公证行", service_types="公证认证", active_tasks=1,
                       payable_month=3800, status="active"),
    ]
    for sp in suppliers:
        s.add(sp)

    sbills = [
        M.TcspSupplierBill(id="SUP-2026-006", supplier_name="金印堂", service_desc="印章制作 ×5 套",
                           amount=4800, period="2026-06", settle_status="待结算"),
        M.TcspSupplierBill(id="SUP-2026-005", supplier_name="正诚公证行", service_desc="公证 ×2",
                           amount=3800, period="2026-06", settle_status="待结算"),
    ]
    for sb in sbills:
        s.add(sb)

    leads = [
        M.TcspLead(customer_name="王先生", source="order_confirm", intent_service="标准注册套餐",
                   status="待跟进", created_at="2026-06-09 13:42"),
        M.TcspLead(customer_name="李女士", source="svc_detail", intent_service="香港移民",
                   status="跟进中", owner="陈顾问", created_at="2026-06-09 11:20"),
        M.TcspLead(customer_name="赵总", source="partner", intent_service="办公租赁",
                   status="已转化", owner="陈顾问", created_at="2026-06-08"),
    ]
    for ld in leads:
        s.add(ld)

    s.commit()
    print("[tcsp_seed] done")
