#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「兴华国际贸易」2025-04 测试数据：10 张票据 + 2 张银行对账单（HTML -> Chrome headless -> PNG）。
与 docs/测试数据_本期交易_兴华贸易_2025-04.md 一致，用于上传解析 / AI 匹配测试。"""
import os, subprocess, tempfile, html

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT    = os.path.join(ROOT, "docs/assets/test_兴华贸易_2025-04")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUR    = "兴华国际贸易有限公司"
OUR_EN = "Sing Wah International Trading Limited"
OUR_BR = "74015288-000-03-25-A"
os.makedirs(OUT, exist_ok=True)

def esc(s): return html.escape(str(s if s is not None else ""))
def money(cur, amt): return f"{cur} " + "{:,.2f}".format(float(amt))

# ───────────────────── 票据数据（10）─────────────────────
INV = [
 dict(id="INV-S01", no="SWI-2025-0401", date="2025-04-03", kind="income",  party="Alpha Electronics Ltd 阿尔法电子",      br="51122334-000-04-24-8", desc="电子产品销售 Sale of electronic goods", cur="HKD", amt=88000),
 dict(id="INV-S02", no="SWI-2025-0402", date="2025-04-18", kind="income",  party="Gamma Tech Co Ltd 伽马科技",           br="52233445-000-02-24-1", desc="电子产品销售 Sale of electronic goods", cur="HKD", amt=120000),
 dict(id="INV-S03", no="SWI-2025-0403", date="2025-04-20", kind="income",  party="Delta Inc (USA) 德尔塔(美国)",          br="US-EIN-88-1234567",    desc="电子产品销售 Sale of electronic goods", cur="USD", amt=15000, note="美元结算 USD settlement"),
 dict(id="INV-S04", no="SWI-2025-0404", date="2025-04-26", kind="income",  party="Echo Trading Ltd 回声贸易",            br="53344556-000-06-24-3", desc="电子产品销售 Sale of electronic goods", cur="HKD", amt=64000, note="月结 30 天 · 赊销 Credit term"),
 dict(id="INV-P01", no="BETA-INV-7781", date="2025-04-07", kind="expense", party="Beta Components Ltd 贝塔元件",          br="60011223-000-03-23-5", desc="采购存货 Purchase of inventory",       cur="HKD", amt=52000),
 dict(id="INV-P02", no="FOX-2025-339",  date="2025-04-24", kind="expense", party="Foxtrot Supplies Ltd 福克斯供应",       br="60122334-000-07-23-9", desc="采购存货 Purchase of inventory",       cur="HKD", amt=38000, note="月结 30 天 · 赊购 Credit term"),
 dict(id="RCPT-R01",no="RENT-2025-04",  date="2025-04-10", kind="receipt", party="Prosper Property Mgmt 富盛物业",        br="61233445-000-01-22-2", desc="办公室租金（四月）Office rent (Apr)",   cur="HKD", amt=18000),
 dict(id="INV-C01", no="SF-HK-90021",   date="2025-04-12", kind="expense", party="SF Express (HK) Ltd 顺丰速运",          br="62344556-000-05-21-7", desc="速递费 Courier charges",               cur="HKD", amt=3200),
 dict(id="INV-T01", no="PCCW-2025-04",  date="2025-04-22", kind="expense", party="PCCW Ltd 电讯盈科",                    br="63455667-000-09-20-4", desc="电话及网络费（四月）Telephone & internet",cur="HKD", amt=1280),
 dict(id="RCPT-M01",no="MX-558203",     date="2025-04-28", kind="receipt", party="Maxim's Restaurant 美心餐厅",          br="64566778-000-11-22-6", desc="业务餐饮招待 Business meal & entertainment", cur="HKD", amt=1500, note="现金 · 董事垫付 Paid by director (cash)"),
]
RECEIPT = {"RCPT-R01", "RCPT-M01"}

CSS_INV = """<style>*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'PingFang HK','Heiti SC',Arial,sans-serif;background:#fff;padding:44px 52px;color:#1a1a1a;width:880px}
.hd{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:3px solid var(--ac);padding-bottom:16px;margin-bottom:22px}
.iss{font-size:20px;font-weight:800;color:var(--ac)}.iss-en{font-size:12.5px;color:#555;margin-top:2px}
.iss-sub{font-size:11.5px;color:#777;margin-top:5px;line-height:1.7}
.ttl{text-align:right}.ttl h1{font-size:24px;letter-spacing:2px;color:var(--ac)}
.ttl .no{font-family:monospace;font-size:13px;margin-top:8px;color:#333}.ttl .dt{font-size:12px;color:#666;margin-top:3px}
.party{display:flex;gap:40px;margin-bottom:20px}.party .box{flex:1}
.lbl{font-size:10px;font-weight:700;color:#999;text-transform:uppercase;letter-spacing:1px;margin-bottom:5px}
.nm{font-size:14px;font-weight:600}.br{font-size:11px;color:#666;margin-top:3px;font-family:monospace}
table{width:100%;border-collapse:collapse;margin-bottom:16px}
th{background:var(--ac);color:#fff;font-size:12px;text-align:left;padding:9px 12px}th.r,td.r{text-align:right}
td{font-size:13px;padding:11px 12px;border-bottom:1px solid #eee}
.sum{display:flex;justify-content:flex-end;margin-bottom:8px}
.sumb{width:300px}.srow{display:flex;justify-content:space-between;font-size:13px;padding:5px 12px}
.stot{display:flex;justify-content:space-between;font-size:16px;font-weight:800;padding:9px 12px;background:#f4f6f9;border-top:2px solid var(--ac)}
.note{font-size:11.5px;color:#7a3e14;background:#fbf3ec;border:1px solid #e8c9b0;border-radius:6px;padding:7px 11px;margin-bottom:10px}
.foot{font-size:10.5px;color:#999;border-top:1px solid #eee;padding-top:12px;line-height:1.8;margin-top:6px}
</style>"""

def invoice_html(d):
    income = d["kind"] == "income"
    ac = "#1F4E8C" if income else "#7A3E14"
    issuer, issuer_en, issuer_br = (OUR, OUR_EN, OUR_BR) if income else (d["party"], "", d["br"])
    billto, billto_br            = (d["party"], d["br"]) if income else (OUR, OUR_BR)
    title = "INVOICE 發票"
    note = f'<div class="note">★ {esc(d.get("note"))}</div>' if d.get("note") else ""
    body = f"""<div class="hd"><div><div class="iss">{esc(issuer)}</div>
      {'<div class="iss-en">'+esc(issuer_en)+'</div>' if issuer_en else ''}
      <div class="iss-sub">BR No.: {esc(issuer_br)}<br>Unit 1208, Tower B, Tsuen Wan, Hong Kong</div></div>
      <div class="ttl"><h1>{title}</h1><div class="no">No. {esc(d['no'])}</div><div class="dt">Date 日期：{esc(d['date'])}</div></div></div>
      <div class="party"><div class="box"><div class="lbl">{'Bill To 客户' if income else 'Supplier 供应商'}</div>
        <div class="nm">{esc(billto if income else issuer)}</div><div class="br">BR: {esc(billto_br if income else issuer_br)}</div></div>
        <div class="box"><div class="lbl">{'Issued By 开票方' if income else 'Bill To 我方'}</div>
        <div class="nm">{esc(issuer if income else billto)}</div><div class="br">BR: {esc(issuer_br if income else billto_br)}</div></div></div>
      {note}
      <table><thead><tr><th>Description 摘要</th><th class="r">Qty</th><th class="r">Amount 金额</th></tr></thead>
      <tbody><tr><td>{esc(d['desc'])}</td><td class="r">1</td><td class="r">{money(d['cur'], d['amt'])}</td></tr></tbody></table>
      <div class="sum"><div class="sumb">
        <div class="srow"><span>Subtotal 小计</span><span>{money(d['cur'], d['amt'])}</span></div>
        <div class="srow"><span>GST/VAT（香港不征）</span><span>—</span></div>
        <div class="stot"><span>TOTAL 合计</span><span>{money(d['cur'], d['amt'])}</span></div></div></div>
      <div class="foot">Currency 币种：{esc(d['cur'])}　|　Payment terms：{esc(d.get('note') or 'Due on receipt')}<br>
      TESTING SAMPLE 测试样本 · {esc(d['id'])} · 香港不征 GST/VAT</div>"""
    return f'<!doctype html><html><head><meta charset="utf-8"><style>:root{{--ac:{ac}}}</style>{CSS_INV}</head><body>{body}</body></html>'

CSS_RCPT = """<style>*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'PingFang HK','Heiti SC',Arial,sans-serif;background:#fafafa;padding:26px;color:#222;width:440px}
.c{background:#fff;border:1px dashed #bbb;padding:24px 26px}
.shop{font-size:18px;font-weight:800;text-align:center}.sub{font-size:11.5px;color:#666;text-align:center;margin-top:3px;line-height:1.6}
.dash{border-top:1px dashed #bbb;margin:14px 0}
.row{display:flex;justify-content:space-between;font-size:12.5px;margin:6px 0}
.item{font-size:13.5px;margin:10px 0;font-weight:600}
.tot{font-size:17px;font-weight:800;display:flex;justify-content:space-between;margin-top:8px}
.foot{text-align:center;font-size:10.5px;color:#888;margin-top:16px;line-height:1.9}</style>"""

def receipt_html(d):
    body = f"""<div class="c"><div class="shop">{esc(d['party'])}</div>
      <div class="sub">BR: {esc(d['br'])} · Hong Kong</div>
      <div class="dash"></div>
      <div class="row"><span>收據編號 Receipt No.</span><span>{esc(d['no'])}</span></div>
      <div class="row"><span>日期 Date</span><span>{esc(d['date'])}</span></div>
      <div class="row"><span>付款方式 Payment</span><span>{'現金 CASH' if 'cash' in (d.get('note','').lower()) or d['id']=='RCPT-M01' else '銀行轉賬 BANK'}</span></div>
      <div class="dash"></div>
      <div class="item">{esc(d['desc'])}</div>
      <div class="row"><span>數量 x1</span><span>{money(d['cur'], d['amt'])}</span></div>
      <div class="dash"></div>
      <div class="tot"><span>合計 TOTAL</span><span>{money(d['cur'], d['amt'])}</span></div>
      <div class="foot">{'Received with thanks 多謝惠顧' }<br>{('★ '+esc(d['note'])) if d.get('note') else ''}<br>
      香港不徵 GST/VAT · TESTING SAMPLE · {esc(d['id'])}</div></div>"""
    return f'<!doctype html><html><head><meta charset="utf-8">{CSS_RCPT}</head><body>{body}</body></html>'

# ───────────────────── 银行对账单（2）─────────────────────
CSS_STMT = """<style>*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'PingFang HK','Heiti SC',Arial,sans-serif;background:#fff;padding:40px 48px;color:#1a1a1a;width:980px}
.hd{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:3px solid #b00;padding-bottom:14px;margin-bottom:8px}
.bank{font-size:19px;font-weight:800;color:#b00}.bank-en{font-size:12px;color:#555;margin-top:2px}
.ttl{text-align:right;font-size:18px;font-weight:800;letter-spacing:1px}
.meta{display:flex;gap:40px;font-size:12px;color:#444;margin:14px 0 16px;line-height:1.8}
.meta b{color:#111}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{background:#f3f4f6;border-bottom:2px solid #999;text-align:left;padding:8px 10px;font-size:11.5px}
th.r,td.r{text-align:right;font-family:monospace}
td{padding:8px 10px;border-bottom:1px solid #eee}
tr.bf td{color:#666;font-style:italic}tr.cf td{font-weight:800;border-top:2px solid #999;background:#f8fafc}
.foot{font-size:10.5px;color:#999;margin-top:14px;line-height:1.8;border-top:1px solid #eee;padding-top:10px}</style>"""

def stmt_html(s):
    rows = ""
    for r in s["rows"]:
        cls = r.get("cls", "")
        rows += f'<tr class="{cls}"><td>{esc(r["date"])}</td><td>{esc(r["desc"])}</td><td class="r">{esc(r.get("out",""))}</td><td class="r">{esc(r.get("in",""))}</td><td class="r">{esc(r["bal"])}</td></tr>'
    body = f"""<div class="hd"><div><div class="bank">{esc(s['bank_zh'])}</div><div class="bank-en">{esc(s['bank_en'])}</div></div>
      <div class="ttl">{esc(s['title'])}</div></div>
      <div class="meta"><div>账户名 Account Name：<b>{OUR}</b><br>账号 Account No.：<b>{esc(s['acct'])}</b></div>
      <div>账单期间 Period：<b>{esc(s['period'])}</b><br>币种 Currency：<b>{esc(s['cur'])}</b></div></div>
      <table><thead><tr><th>Date 日期</th><th>Description 摘要</th><th class="r">Withdrawal 支出</th><th class="r">Deposit 存入</th><th class="r">Balance 余额</th></tr></thead>
      <tbody>{rows}</tbody></table>
      <div class="foot">本对账单为<b>测试样本 TESTING SAMPLE</b>，账号/数字均为虚构。币种 {esc(s['cur'])}。<br>This is a computer-generated statement for testing — no signature required.</div>"""
    return f'<!doctype html><html><head><meta charset="utf-8">{CSS_STMT}</head><body>{body}</body></html>'

STMT = [
 dict(file="BANK-HSBC-1002-01", bank_zh="香港上海滙豐銀行有限公司", bank_en="The Hongkong and Shanghai Banking Corporation Limited",
      title="STATEMENT OF ACCOUNT 月結單", acct="456-789012-838", period="01 Apr 2025 – 30 Apr 2025", cur="HKD", size="980,720", rows=[
   dict(date="2025-04-01", desc="Balance brought forward 承上结余", bal="285,000.00", cls="bf"),
   dict(date="2025-04-03", desc="INWARD CREDIT — ALPHA ELECTRONICS",   **{"in":"88,000.00"},  bal="373,000.00"),
   dict(date="2025-04-07", desc="OUTWARD PAYMENT — BETA COMPONENTS",   out="52,000.00",        bal="321,000.00"),
   dict(date="2025-04-10", desc="RENT — PROSPER PROPERTY MGMT",        out="18,000.00",        bal="303,000.00"),
   dict(date="2025-04-12", desc="COURIER — SF EXPRESS",                out="3,200.00",         bal="299,800.00"),
   dict(date="2025-04-15", desc="PAYROLL — SALARIES (APR)",            out="45,000.00",        bal="254,800.00"),
   dict(date="2025-04-18", desc="INWARD CREDIT — GAMMA TECH",          **{"in":"120,000.00"}, bal="374,800.00"),
   dict(date="2025-04-22", desc="DIRECT DEBIT — PCCW",                 out="1,280.00",         bal="373,520.00"),
   dict(date="2025-04-25", desc="SERVICE CHARGE 服务费",               out="180.00",           bal="373,340.00"),
   dict(date="2025-04-30", desc="CREDIT INTEREST 存款利息",            **{"in":"95.00"},      bal="373,435.00"),
   dict(date="2025-04-30", desc="Balance carried forward 结转下期",     bal="373,435.00", cls="cf"),
 ]),
 dict(file="BANK-BOC-1002-03-USD", bank_zh="中國銀行(香港)有限公司", bank_en="Bank of China (Hong Kong) Limited",
      title="USD STATEMENT 美元月結單", acct="012-883-7654321", period="01 Apr 2025 – 30 Apr 2025", cur="USD", size="980,460", rows=[
   dict(date="2025-04-01", desc="Balance brought forward 承上结余", bal="20,000.00", cls="bf"),
   dict(date="2025-04-20", desc="INWARD T/T — DELTA INC (USA)",   **{"in":"15,000.00"}, bal="35,000.00"),
   dict(date="2025-04-30", desc="Balance carried forward 结转下期", bal="35,000.00", cls="cf"),
 ]),
]

def render(htmlf_name, html_str, pngf_name, size):
    htmlf = os.path.join(tempfile.gettempdir(), htmlf_name + ".html")
    pngf  = os.path.join(OUT, pngf_name + ".png")
    open(htmlf, "w", encoding="utf-8").write(html_str)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--default-background-color=FFFFFFFF",
                    f"--window-size={size}", f"--screenshot={pngf}", "file://" + htmlf],
                   capture_output=True, timeout=60)
    return os.path.exists(pngf)

def main():
    ok = 0
    for d in INV:
        is_r = d["id"] in RECEIPT
        h = receipt_html(d) if is_r else invoice_html(d)
        size = "440,720" if is_r else "920,860"
        name = f"{d['id']}_{d['no'].replace('/','-')}"
        if render(name, h, name, size): ok += 1; print("✓ 票据", name)
        else: print("✗ 失败", d["id"])
    for s in STMT:
        if render(s["file"], stmt_html(s), s["file"], s["size"]): ok += 1; print("✓ 对账单", s["file"])
        else: print("✗ 失败", s["file"])
    print(f"\n生成 {ok} 张图片 -> {OUT}")

if __name__ == "__main__":
    main()
