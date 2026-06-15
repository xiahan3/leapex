"""Seed initial data from the EasybookX-1.11.html prototype.

COA loaded from coa_seed.json (sibling file).
Other entities are inlined.
"""
import json
import os
from pathlib import Path
from sqlmodel import Session
from . import models as M

DATA_DIR = Path(__file__).parent / "data"


def run(s: Session):
    # ── COA ─────────────────────────────────────────────────────────
    coa_path = DATA_DIR / "coa_seed.json"
    if coa_path.exists():
        for r in json.loads(coa_path.read_text()):
            s.add(M.COA(**r))
    s.commit()

    # ── Bank statements (BK_LIST + STAGED_BK) ───────────────────────
    bk = [
        dict(id="bk1", filename="HSBC_Statement_2025-11.pdf", bank="HSBC", bank_color="#DB0011",
             acct_no="012-345678-001", acct_type="往来账户", period="2025-11",
             txn_count=14, end_balance="HKD 54,820.00", month_label="2025年11月", status="done"),
        dict(id="bk2", filename="HSBC_Statement_2025-12.pdf", bank="HSBC", bank_color="#DB0011",
             acct_no="012-345678-001", acct_type="往来账户", period="2025-12",
             txn_count=18, end_balance="HKD 41,220.50", month_label="2025年12月", status="done"),
        dict(id="bk3", filename="HS_Dec2025_eStatement.pdf", bank="恒生", bank_color="#E30613",
             acct_no="888-123456-838", acct_type="储蓄账户", period="2025-12",
             txn_count=10, end_balance="HKD 15,800.00", month_label="2025年12月", status="done"),
        # Staged
        dict(id="sb1", filename="HSBC_Feb2026_complete.pdf", bank="HSBC", bank_color="#DB0011",
             acct_no="", acct_type="往来账户", period="2026-02",
             txn_count=0, end_balance=None, month_label="2026年2月", status="parsing",
             stage="staged", is_own=True, company="ABC Trading Co. Ltd",
             pages=7, total_pages=7),
        dict(id="sb2", filename="bank_statement_HKVentures.pdf", bank="HSBC", bank_color="#DB0011",
             acct_no="", acct_type="往来账户", period="2026-02",
             txn_count=0, end_balance=None, month_label="2026年2月", status="parsing",
             stage="staged", is_own=False, company="HK Ventures Ltd",
             note="对账单抬头检测为 HK Ventures Ltd，与当前账套不符",
             pages=3, total_pages=None),
    ]
    for r in bk:
        s.add(M.BankStatement(**r))
    s.commit()

    # ── Invoices ────────────────────────────────────────────────────
    INV_DATA = {
        "2025-11": [
            ("A1","電訊盈科 PCCW","INV-2511-018","Telephone","2025-11-08","HKD 488.00",98,"done","expense","matched"),
            ("A2","中国石化","RCP-1115-021","Fuel","2025-11-15","HKD 305.20",95,"done","expense","matched"),
            ("A3","惠康超市","—","Office supplies","2025-11-22","HKD 189.60",91,"done","expense","unmatched"),
        ],
        "2025-12": [
            ("B1","中国石化","RCP-1210-003","Fuel","2025-12-10","HKD 312.00",96,"done","expense","matched"),
            ("B2","美心餐廳","RCP-1218-007","Meals","2025-12-18","HKD 620.00",88,"done","expense","matched"),
            ("B3","UPS Hong Kong","UPS-DEC-8821","Postage","2025-12-20","USD 78.40",94,"done","expense","matched"),
            ("B4","手写小票","—","Other","2025-12-28","HKD 90.00",55,"review","expense","unmatched"),
            ("B5","ABC Trading Co.","SI-2512-001","Sales Invoice","2025-12-05","HKD 8,500.00",97,"done","income","matched"),
        ],
        "2026-01": [
            ("C1","電訊盈科 PCCW","INV-2601-018","Telephone","2026-01-08","HKD 488.00",98,"done","expense","matched"),
            ("C2","中国石化","RCP-0115-022","Fuel","2026-01-15","HKD 321.50",96,"done","expense","matched"),
            ("C3","九記茶餐廳","—","Meals","2026-01-12","HKD 145.00",62,"review","expense","orphan"),
            ("C4","香港的士 ×2","—","Travelling expenses","2026-01-20","HKD 500.00",91,"merge","expense","pending"),
            ("C5","商務印書館","RI-2601-0091","Office supplies","2026-01-22","HKD 236.00",93,"done","expense","matched"),
            ("C6","Peak View Ltd","SI-2601-001","Sales Invoice","2026-01-10","HKD 15,200.00",99,"done","income","matched"),
        ],
        "2026-02": [
            ("D1","中国石化","RCP-0205-003","Fuel","2026-02-05","HKD 298.00",97,"done","expense","matched"),
            ("D2","電訊盈科 PCCW","INV-2602-018","Telephone","2026-02-08","HKD 488.00",98,"done","expense","unmatched"),
        ],
    }
    for period, rows in INV_DATA.items():
        for (iid, merchant, no, cat, date, amt, conf, status, itype, recon_st) in rows:
            s.add(M.Invoice(
                id=iid, period=period, merchant=merchant, invoice_no=no, category=cat,
                invoice_date=date, amt=amt, ai_confidence=conf, parse_status=status,
                invoice_type=itype, recon_state=recon_st, stage="parsed", is_own=True,
            ))

    # Staged invoices
    staged = [
        ("si1","receipt_sinopec_jan20.jpg","2026-01-22 09:32","ABC Trading Co. Ltd","中国石化（香港）有限公司","expense",True,"done",94,False,None,None),
        ("si2","invoice_PCCW_Jan2026.pdf","2026-01-22 09:35","ABC Trading Co. Ltd","電訊盈科 PCCW Ltd","expense",True,"done",97,False,None,None),
        ("si5","invoice_PCCW_Jan2026_v2.pdf","2026-01-22 10:15","ABC Trading Co. Ltd","電訊盈科 PCCW Ltd","expense",True,"done",95,True,
            "⚠ 疑似重复 — 与已上传 PCCW Jan 2026 发票金额相同，建议确认是否为同一张",None),
        ("si6","HKE_electricity_Jan2026.pdf","2026-01-22 10:22","ABC Holdings Ltd","香港電燈有限公司","expense",False,"done",91,False,
            "⚠ 非本公司票据 — 发票抬头为 ABC Holdings Ltd，与当前账套 ABC Trading Co. Ltd 不符",None),
        ("si3","sales_invoice_to_peakview.pdf","2026-01-22 09:41","Peak View Ltd","Peak View Ltd","income",False,"done",88,False,
            "发票抬头为 Peak View Ltd，与当前账套不符",None),
        ("si4","handwritten_receipt_0122.png","2026-01-22 09:45","ABC Trading Co. Ltd","待识别","unknown",True,"failed",42,False,
            None,"手写字迹模糊，OCR置信度42%，建议重新扫描或手工录入"),
    ]
    for (iid, fname, uat, mycomp, cpty, itype, isown, ust, conf, isdup, note, err) in staged:
        s.add(M.Invoice(
            id=iid, stage="staged", filename=fname, upload_at=uat,
            my_company=mycomp, counterparty=cpty, invoice_type=itype,
            is_own=isown, upload_st=ust, ai_confidence=conf, is_duplicate=isdup,
            note=note, upload_err=err, parse_status=ust,
        ))
    s.commit()

    # ── Recon Pairs ─────────────────────────────────────────────────
    RECON_PAIRS = {
        "2026-01": [
            dict(st="match", txn=dict(desc="PCCW*TELECOM AUTOPAY JAN", date="01-08", amt="488.00", dir="out"),
                 invs=[dict(desc="電訊盈科 Invoice #INV2026018", amt="488.00", type="expense")]),
            dict(st="match", txn=dict(desc="SINOPEC FUEL STATION 518", date="01-15", amt="321.50", dir="out"),
                 invs=[dict(desc="中石化加油小票", amt="321.50", type="expense")]),
            dict(st="match", txn=dict(desc="UPS EXPRESS FREIGHT", date="01-05", amt="611.20", dir="out"),
                 invs=[dict(desc="UPS HK — Shipping Invoice", amt="611.20", type="expense")]),
            dict(st="match", txn=dict(desc="COMMERCIAL PRESS 商務印書館", date="01-22", amt="236.00", dir="out"),
                 invs=[dict(desc="商務印書館收据", amt="236.00", type="expense")]),
            dict(st="match", txn=dict(desc="BANK CHARGE 银行手续费", date="01-31", amt="150.00", dir="out"),
                 invs=[dict(desc="银行手续费（免票据）", amt="150.00", type="expense")]),
            dict(st="match", txn=dict(desc="CUSTOMER PMT / PEAK VIEW", date="01-03", amt="8,500.00", dir="in"),
                 invs=[dict(desc="Sales Invoice #SI-2601 — Peak View", amt="8,500.00", type="income")]),
            dict(st="match", txn=dict(desc="CUSTOMER PMT / HK VENTURES", date="01-10", amt="15,200.00", dir="in"),
                 invs=[dict(desc="Sales Invoice #SI-2602 — HK Ventures", amt="15,200.00", type="income")]),
            dict(st="match", txn=dict(desc="CUSTOMER PMT / FORTUNE INTL", date="01-25", amt="22,100.00", dir="in"),
                 invs=[dict(desc="Sales Invoice #SI-2603 — Fortune Intl", amt="22,100.00", type="income")]),
            dict(st="match", txn=dict(desc="INTEREST INCOME", date="01-31", amt="18.50", dir="in"),
                 invs=[dict(desc="利息收入（无需票据）", amt="18.50", type="income")]),
            dict(st="match", txn=dict(desc="TAXI FARE PAYMENT APP", date="01-20", amt="500.00", dir="out"),
                 invs=[dict(desc="的士票 A — 01-20", amt="250.00", type="expense"),
                       dict(desc="的士票 B — 01-20", amt="250.00", type="expense")]),
            dict(st="unmatched", txn=dict(desc="UNKNOWN VENDOR TRF", date="01-18", amt="1,200.00", dir="out"), invs=[]),
            dict(st="unmatched", txn=dict(desc="UNKNOWN REMITTANCE — REF 8821", date="01-26", amt="12,000.00", dir="in"), invs=[],
                 unmatchedNote="已收银行款项但未能找到对应收入发票，请确认客户及开票情况"),
            dict(st="orphan", txn=None, invs=[dict(desc="九記茶餐廳（手写）", amt="145.00", type="expense", orphanNote="无对应流水，现金或私人垫付")]),
            dict(st="orphan", txn=None, invs=[dict(desc="停车场收据（现金）", amt="80.00", type="expense", orphanNote="无对应流水，现金付款")]),
            dict(st="orphan", txn=None, invs=[dict(desc="Sales Invoice #SI-2605 — Sunrise Holdings Ltd", amt="18,500.00", type="income",
                 orphanNote="已开票未收款 · 应收账款 Accounts Receivable · 请确认付款时间")]),
        ],
        "2025-12": [
            dict(st="match", txn=dict(desc="PCCW*TELECOM AUTOPAY DEC", date="12-08", amt="488.00", dir="out"),
                 invs=[dict(desc="電訊盈科 Invoice Dec", amt="488.00", type="expense")]),
            dict(st="match", txn=dict(desc="SINOPEC FUEL STN 210", date="12-10", amt="312.00", dir="out"),
                 invs=[dict(desc="中石化加油小票", amt="312.00", type="expense")]),
            dict(st="unmatched", txn=dict(desc="UNKNOWN TRANSFER", date="12-28", amt="850.00", dir="out"), invs=[]),
        ],
        "2025-11": [
            dict(st="match", txn=dict(desc="PCCW*TELECOM AUTOPAY NOV", date="11-08", amt="488.00", dir="out"),
                 invs=[dict(desc="電訊盈科 Invoice Nov", amt="488.00", type="expense")]),
            dict(st="match", txn=dict(desc="SINOPEC FUEL STN 518", date="11-15", amt="305.20", dir="out"),
                 invs=[dict(desc="中石化加油小票", amt="305.20", type="expense")]),
            dict(st="unmatched", txn=dict(desc="WELLCOME SUPERMARKET", date="11-22", amt="189.60", dir="out"), invs=[]),
        ],
        "2026-02": [
            dict(st="match", txn=dict(desc="PCCW*TELECOM AUTOPAY FEB", date="02-08", amt="488.00", dir="out"),
                 invs=[dict(desc="電訊盈科 Invoice Feb", amt="488.00", type="expense")]),
            dict(st="match", txn=dict(desc="SINOPEC FUEL STN 518", date="02-05", amt="298.00", dir="out"),
                 invs=[dict(desc="中石化加油小票", amt="298.00", type="expense")]),
        ],
    }
    for period, pairs in RECON_PAIRS.items():
        for i, p in enumerate(pairs):
            s.add(M.ReconPair(
                period=period, pair_index=i,
                status=p["st"], txn=p.get("txn"), invs=p.get("invs", []),
                unmatched_note=p.get("unmatchedNote"),
            ))
    s.commit()

    # ── Journal Entries ─────────────────────────────────────────────
    je_seed = [
        ("JV-2026-001","2026-01-15","Motor vehicle expenses — Sinopec Fuel Station","confirmed",
         [{"type":"Dr","account":"Motor vehicle expenses","amount":321.50},
          {"type":"Cr","account":"Bank — HSBC Current Account","amount":321.50}]),
        ("JV-2026-002","2026-01-08","Telephone and internet — PCCW monthly autopay Jan 2026","confirmed",
         [{"type":"Dr","account":"Telephone and internet","amount":488.00},
          {"type":"Cr","account":"Bank — HSBC Current Account","amount":488.00}]),
        ("JV-2026-003","2026-01-05","Postage and courier — UPS Express International shipment","confirmed",
         [{"type":"Dr","account":"Postage and courier","amount":611.20},
          {"type":"Cr","account":"Bank — HSBC Current Account","amount":611.20}]),
        ("JV-2026-004","2026-01-22","Office supplies — Commercial Press 商務印書館 stationery","confirmed",
         [{"type":"Dr","account":"Office supplies","amount":236.00},
          {"type":"Cr","account":"Bank — HSBC Current Account","amount":236.00}]),
        ("JV-2026-005","2026-01-31","Bank charges — HSBC current account monthly service fee","confirmed",
         [{"type":"Dr","account":"Bank charges","amount":150.00},
          {"type":"Cr","account":"Bank — HSBC Current Account","amount":150.00}]),
        ("JV-2026-006","2026-01-20","Travelling expenses — Taxi fares Jan 2026 (2 receipts merged)","confirmed",
         [{"type":"Dr","account":"Travelling expenses","amount":500.00},
          {"type":"Cr","account":"Bank — HSBC Current Account","amount":500.00}]),
        ("JV-2026-007","2026-01-03","Revenue — Professional services, Peak View Properties Ltd","confirmed",
         [{"type":"Dr","account":"Bank — HSBC Current Account","amount":8500.00},
          {"type":"Cr","account":"Revenue from rendering of services","amount":8500.00}]),
        ("JV-2026-008","2026-01-10","Revenue — Professional services, HK Ventures Ltd","confirmed",
         [{"type":"Dr","account":"Bank — HSBC Current Account","amount":15200.00},
          {"type":"Cr","account":"Revenue from rendering of services","amount":15200.00}]),
        ("JV-2026-009","2026-01-25","Revenue — Professional services, Fortune International Ltd","confirmed",
         [{"type":"Dr","account":"Bank — HSBC Current Account","amount":22100.00},
          {"type":"Cr","account":"Revenue from rendering of services","amount":22100.00}]),
        ("JV-2026-010","2026-01-31","Interest income — HSBC current account interest Jan 2026","confirmed",
         [{"type":"Dr","account":"Bank — HSBC Current Account","amount":18.50},
          {"type":"Cr","account":"Interest income","amount":18.50}]),
        ("JV-2026-011","2026-01-12","Meals and entertainment — Business lunch, director's advance","pending",
         [{"type":"Dr","account":"Meals and entertainment","amount":145.00},
          {"type":"Cr","account":"Director's Current Account","amount":145.00}]),
        ("JV-2026-012","2026-01-20","Travelling expenses — Parking fee, petty cash reimbursement","pending",
         [{"type":"Dr","account":"Travelling expenses","amount":80.00},
          {"type":"Cr","account":"Petty Cash — Office","amount":80.00}]),
        ("JV-2026-013","2026-01-31","Depreciation — Office equipment Jan 2026 (Step 3 period-end adjustment)","pending",
         [{"type":"Dr","account":"Depreciation and amortisation","amount":400.00},
          {"type":"Cr","account":"Accumulated depreciation — Property and equipment","amount":400.00}]),
    ]
    for jid, dt, desc, status, lines in je_seed:
        s.add(M.JournalEntry(id=jid, entry_date=dt, description=desc, status=status, lines=lines, source="recon"))
    s.commit()

    # ── Cash Entries ────────────────────────────────────────────────
    cash = [
        ("cash1","2026-01-06","的士费（旺角→中环客户会面）","expense","6234","1003-01","HKD",82.00,"matched","","客户会面交通，现金付款，保留收据"),
        ("cash2","2026-01-10","Wellcome 超市办公用品","expense","6220","1003-01","HKD",58.50,"matched","","文具、打印纸、胶带"),
        ("cash3","2026-01-15","商务工作午餐（City Hall Maxim's）","expense","6233","2251-01","HKD",680.00,"matched","","接待客户 Peak View Properties，共 4 人，董事先生代付"),
        ("cash7","2026-01-12","现金收款 — Peak View 服务费尾款（Peak View Properties Ltd）","income","1003-01","4005","HKD",3500.00,"matched","JV-2026-101","对应发票 SI-2025-088 尾款，现金收讫已存保险箱"),
        ("cash8","2026-01-20","HSBC 储蓄账户利息收入（HSBC）","income","1002-01","4101","HKD",128.45,"orphan","","2025-Q4 储蓄利息，月结单第3页"),
        ("cash4","2026-01-18","停车场月费（皇后大道中停车场）","expense","6219","2251-01","HKD",2200.00,"orphan","","公司用车停车月费，董事代付，月底报销"),
        ("cash5","2026-01-22","快递费（DHL 寄合同至上海）","expense","6232","1003-01","HKD",245.00,"orphan","","合同原件快递，保留收件编号"),
        ("cash6","2026-01-28","HKICPA 年费（香港会计师公会）","expense","6215","2251-01","HKD",1800.00,"orphan","","CPA 年度会籍费用，董事代付，税务可扣除"),
    ]
    for cid, dt, desc, etype, dr, cr, curr, amt, recon, voucher, notes in cash:
        s.add(M.CashEntry(id=cid, date=dt, desc=desc, entry_type=etype,
                          dr_code=dr, cr_code=cr, currency=curr, amt=amt,
                          recon_st=recon, voucher=voucher, notes=notes))
    s.commit()

    # ── Adjustments ─────────────────────────────────────────────────
    adj = [
        ("ADJ-001","dep","Depreciation and amortisation (6236)","Accumulated depreciation — PPE (1660)",400.00,
         "Office equipment depreciation Jan 2026 (cost HKD 4,800 ÷ 12 mths)","confirmed"),
        ("ADJ-002","accrued","Audit fee (6201)","Accrued charges (2150)",5000.00,
         "Accrued annual audit fee — est. HKD 60,000 p.a. ÷ 12","pending"),
        ("ADJ-003","accrued","MPF contributions (6230)","Accrued charges (2150)",1500.00,
         "Accrued employer MPF contribution Jan 2026 (1 employee × HKD 1,500 cap)","pending"),
        ("ADJ-004","tax","Profits tax expense (7100)","Tax payable (2200)",3538.16,
         "Estimated profits tax provision — 8.25% on first HKD 2M assessable profit","pending"),
    ]
    for aid, cat, dr, cr, amt, desc, status in adj:
        s.add(M.AdjEntry(id=aid, period="2026-01", cat=cat, dr_acct=dr, cr_acct=cr,
                         amt=amt, desc=desc, status=status))
    s.commit()

    # ── Company Profile ─────────────────────────────────────────────
    s.add(M.CompanyProfile(
        company_id="ABC", name="ABC Trading Co. Ltd",
        br_no="12345678-000-01-26-3", fy_start_month=7, first_period="2025-07 至 2026-06",
        base_currency="HKD", closing_freq="quarterly",
    ))
    s.commit()

    # ── 平台管理：Tenants ───────────────────────────────────────────
    tenants = [
        dict(id="T-2026-0001", name="ABC CPA Limited", type="CPA Firm", plan="Professional", companies=8, users=12, token_used=124700, token_quota=200000, mrr=980, status="active", status_pill="p-green", br_no="1234567", contact="陈大文 Andy Chan", email="andy@abccpa.hk", phone="+852 9123 4567", created_at="2025-08-12", expire_at="2026-06-22"),
        dict(id="T-2026-0002", name="Sunrise CPA Limited", type="CPA Firm", plan="Professional", companies=10, users=14, token_used=183600, token_quota=200000, mrr=980, status="active", status_pill="p-amber", br_no="2345678", contact="李明 Sunny Lee", email="admin@sunrisecpa.hk", phone="+852 9234 5678", created_at="2025-09-01", expire_at="2026-07-01"),
        dict(id="T-2026-0003", name="Vantage CPA Group", type="CPA Firm", plan="Firm", companies=42, users=48, token_used=93950, token_quota=800000, mrr=2580, status="active", status_pill="p-green", br_no="3456789", contact="黄国强 K.K. Wong", email="ops@vantage.hk", phone="+852 9345 6789", created_at="2025-05-20", expire_at="2026-09-15"),
        dict(id="T-2026-0004", name="HK Bookkeep Co.", type="独立 SME", plan="Starter", companies=3, users=5, token_used=26000, token_quota=50000, mrr=380, status="suspended", status_pill="p-red", br_no="4567890", contact="张伟 Wilson Cheung", email="info@hkbookkeep.hk", phone="+852 9456 7890", created_at="2026-01-10", expire_at="2026-06-06"),
        dict(id="T-2026-0005", name="Peak Finance Ltd", type="企业集团", plan="Starter", companies=2, users=4, token_used=8200, token_quota=50000, mrr=380, status="active", status_pill="p-green", br_no="5678901", contact="刘德 Derek Lau", email="finance@peakfin.hk", phone="+852 9567 8901", created_at="2026-02-15", expire_at="2026-08-01"),
        dict(id="T-2026-0006", name="TaiKai 太楷簿记", type="CPA Firm", plan="Trial", companies=1, users=2, token_used=1200, token_quota=5000, mrr=0, status="trial", status_pill="p-blue", br_no="6789012", contact="陈太楷 Taikai Chan", email="hello@taikai.hk", phone="+852 9678 9012", created_at="2026-06-01", expire_at="2026-06-15"),
    ]
    for t in tenants:
        s.add(M.Tenant(**t))
    s.commit()

    # ── 平台管理：Tenant Users ──────────────────────────────────────
    users = [
        dict(id="U-2026-00001", name="陈大文 Andy Chan", email="andy@abccpa.hk", phone="+852 9123 4567", role="tenant_admin", companies=8, last="刚刚", status="active", twofa=True, is_self=True),
        dict(id="U-2026-00002", name="李四 Sue Li", email="siu@abccpa.hk", phone="+852 9234 5678", role="bookkeeper", companies=3, last="5 分钟前", status="active", twofa=False),
        dict(id="U-2026-00003", name="王五 Wang Wu", email="wang@abccpa.hk", phone="+852 9345 6789", role="reviewer", companies=2, last="3 天前", status="active", twofa=True),
        dict(id="U-2026-00004", name="周六 Joe Chow", email="joe@abccpa.hk", phone="", role="senior", companies=5, last="1 小时前", status="active", twofa=False),
        dict(id="U-2026-00005", name="吴七 Vivian Ng", email="vivian@abccpa.hk", phone="+852 9456 7890", role="bookkeeper", companies=2, last="昨天", status="active", twofa=False),
        dict(id="U-2026-00006", name="郑八 Tony Cheng", email="tony@abccpa.hk", phone="", role="viewer", companies=1, last="5 天前", status="active", twofa=False),
        dict(id="U-2026-00007", name="刘九 Linda Liu", email="linda@abccpa.hk", phone="", role="reviewer", companies=3, last="8 小时前", status="active", twofa=True),
        dict(id="U-2026-00008", name="张三 Cody Cheung", email="cody@abccpa.hk", phone="", role="viewer", companies=1, last="30 天前", status="disabled", twofa=False),
        dict(id="U-2026-00009", name="Mary 新员工", email="mary@abccpa.hk", phone="", role="bookkeeper", companies=1, last="未激活", status="invited", twofa=False),
        dict(id="U-2026-00010", name="Peter (邀请中)", email="peter@abccpa.hk", phone="", role="viewer", companies=2, last="未激活", status="invited", twofa=False),
    ]
    for u in users:
        s.add(M.TenantUser(**u))
    s.commit()

    # ── 平台管理：Plans ─────────────────────────────────────────────
    plans = [
        dict(key="trial", name="Trial 试用", price=0, unit="/ 14 天", max_companies="1", max_users="2", token_quota="5000", features=["全部 AI 功能"], rec=False, sort_order=1),
        dict(key="starter", name="Starter", price=380, unit="/ 月", max_companies="3", max_users="5", token_quota="50000", features=["全部 AI 功能"], rec=False, sort_order=2),
        dict(key="pro", name="Professional", price=980, unit="/ 月", max_companies="10", max_users="15", token_quota="200000", features=["优先客服 + 培训"], rec=True, sort_order=3),
        dict(key="firm", name="Firm", price=2580, unit="/ 月", max_companies="50", max_users="50", token_quota="800000", features=["专属客户经理"], rec=False, sort_order=4),
        dict(key="ent", name="Enterprise", price=None, unit="", max_companies="不限", max_users="不限", token_quota="按需", features=["私有部署可选"], rec=False, sort_order=5),
    ]
    for p in plans:
        s.add(M.Plan(**p))
    s.commit()

    # ── 平台管理：Billing Invoices ──────────────────────────────────
    bills = [
        dict(no="INV-2026-05-T0001", tenant="ABC CPA Limited", plan="Professional", total=1182.69, subtotal=1314.10, discount=131.41, method="线下转账", channel="offline", status="proof_uploaded", period="2026-05",
             items=[["订阅费 · Professional 套餐","月费","980.00"],["银行流水 OCR 超额","320 页 × HKD 0.005","1.60"],["票据 OCR 超额","1,240 张 × 50 × 0.005","310.00"],["AI 财务分析报告","2 份 × 2000 × 0.005","20.00"],["AI 异常检测","1 次 × 500 × 0.005","2.50"]]),
        dict(no="INV-2026-05-T0002", tenant="Sunrise CPA Limited", plan="Professional", total=1458.00, subtotal=1458.00, discount=0, method="FPS 转数快", channel="online", status="paid", period="2026-05",
             items=[["订阅费 · Professional 套餐","月费","980.00"],["票据 OCR 超额","1,840 张 × 50 × 0.005","460.00"],["AI 异常检测","—","18.00"]]),
        dict(no="INV-2026-05-T0003", tenant="Vantage CPA Group", plan="Firm", total=2580.00, subtotal=2580.00, discount=0, method="信用卡", channel="online", status="paid", period="2026-05",
             items=[["订阅费 · Firm 套餐","月费","2,580.00"]]),
        dict(no="INV-2026-05-T0004", tenant="Peak Finance Ltd", plan="Starter", total=380.00, subtotal=380.00, discount=0, method="—", channel="offline", status="issued", period="2026-05",
             items=[["订阅费 · Starter 套餐","月费","380.00"]]),
        dict(no="INV-2026-05-T0005", tenant="HK Bookkeep Co.", plan="Starter", total=980.00, subtotal=980.00, discount=0, method="—", channel="offline", status="overdue", period="2026-04",
             items=[["订阅费 · Starter 套餐（含上期欠款）","月费 380 + 上期 600","980.00"]]),
        dict(no="INV-2026-05-T0006", tenant="ABC CPA Limited", plan="Professional", total=980.00, subtotal=980.00, discount=0, method="FPS 转数快", channel="online", status="paid", period="2026-04",
             items=[["订阅费 · Professional 套餐","月费","980.00"]]),
    ]
    for b in bills:
        s.add(M.BillingInvoice(**b))
    s.commit()

    # ── 平台管理：Audit Reports（历史记录）─────────────────────────
    reports = [
        dict(no="AR-2026-0007", company="ABC Trading Co. Ltd", company_id="abc", period="FY2025/26", report_type="审前分析报告", framework="SME-FRS", score=87),
        dict(no="AR-2026-0005", company="HK Ventures Ltd", company_id="hkv", period="FY2025/26", report_type="审计辅助底稿", framework="HKFRS", score=93),
    ]
    for r in reports:
        s.add(M.AuditReport(**r))
    s.commit()

    print("[seed] done")
