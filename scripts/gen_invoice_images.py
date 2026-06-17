#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 HSBC 测试票据 JSON 渲染为仿真票据图片（HTML -> Chrome headless -> PNG）。
用于 OCR 上传解析的测试验证。"""
import json, os, subprocess, html, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "backend/data/test_invoices_hsbc_456459775838.json")
OUT  = os.path.join(ROOT, "docs/assets/test_invoices")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUR = "ABC Trading Co. Ltd  ABC 貿易有限公司"
OUR_BR = "63920011-000-05-25-1"

os.makedirs(OUT, exist_ok=True)

# 小票版式（现金/餐饮/停车）
RECEIPT_IDS = {"TINV-009", "TINV-010"}

def esc(s): return html.escape(str(s if s is not None else ""))

def money(cur, amt):
    try: v = "{:,.2f}".format(float(amt))
    except Exception: v = str(amt)
    return f"{cur} {v}"

def invoice_html(inv):
    income = inv.get("invoice_type") == "income"
    cur = inv.get("currency", "HKD")
    # 收入=我方开票给客户；支出=供应商开票给我方
    issuer   = OUR if income else inv["merchant"]
    issuerBr = OUR_BR if income else inv.get("br_no", "")
    billto   = inv["merchant"] if income else OUR
    billtoBr = inv.get("br_no", "") if income else OUR_BR
    title    = "INVOICE 發票" if income else ("RECEIPT 收據" if inv["id"] in RECEIPT_IDS else "INVOICE 發票")
    accent   = "#1F4E8C" if income else "#7A3E14"
    desc     = inv.get("category", "")
    summ     = inv.get("_summary", "")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'PingFang HK','Heiti SC','Microsoft YaHei',Arial,sans-serif;background:#fff;padding:46px 54px;color:#1a1a1a;width:820px}}
.hd{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:3px solid {accent};padding-bottom:16px;margin-bottom:22px}}
.iss{{font-size:21px;font-weight:800;color:{accent}}}
.iss-sub{{font-size:12px;color:#666;margin-top:4px;line-height:1.7}}
.ttl{{text-align:right}}
.ttl h1{{font-size:25px;letter-spacing:2px;color:{accent}}}
.ttl .no{{font-family:monospace;font-size:13px;margin-top:8px;color:#333}}
.ttl .dt{{font-size:12px;color:#666;margin-top:3px}}
.party{{display:flex;gap:40px;margin-bottom:22px}}
.party .box{{flex:1}}
.lbl{{font-size:10.5px;font-weight:700;color:#999;text-transform:uppercase;letter-spacing:1px;margin-bottom:5px}}
.nm{{font-size:14px;font-weight:600}}
.br{{font-size:11.5px;color:#666;margin-top:3px;font-family:monospace}}
table{{width:100%;border-collapse:collapse;margin-bottom:18px}}
th{{background:{accent};color:#fff;font-size:12px;text-align:left;padding:9px 12px}}
th.r,td.r{{text-align:right}}
td{{padding:12px;border-bottom:1px solid #eee;font-size:13px}}
.tot{{display:flex;justify-content:flex-end}}
.tot .t{{width:300px}}
.tot .row{{display:flex;justify-content:space-between;padding:7px 0;font-size:13px}}
.tot .grand{{border-top:2px solid {accent};font-weight:800;font-size:18px;color:{accent};padding-top:10px;margin-top:4px}}
.note{{margin-top:26px;font-size:11.5px;color:#777;border-top:1px dashed #ccc;padding-top:12px;line-height:1.7}}
.foot{{margin-top:14px;font-size:10.5px;color:#aaa;text-align:center}}
.gst{{font-size:10.5px;color:#999;margin-top:4px}}
</style></head><body>
<div class="hd">
  <div><div class="iss">{esc(issuer)}</div><div class="iss-sub">商業登記號 BR No: {esc(issuerBr)}<br>Hong Kong · 香港</div></div>
  <div class="ttl"><h1>{title}</h1><div class="no">No. {esc(inv.get('invoice_no'))}</div><div class="dt">Date 日期: {esc(inv.get('invoice_date'))}</div></div>
</div>
<div class="party">
  <div class="box"><div class="lbl">{'From 開票方' if income else 'Supplier 供應商'}</div><div class="nm">{esc(issuer)}</div><div class="br">BR: {esc(issuerBr)}</div></div>
  <div class="box"><div class="lbl">{'Bill To 客戶' if income else 'Bill To 客戶（本公司）'}</div><div class="nm">{esc(billto)}</div><div class="br">BR: {esc(billtoBr)}</div></div>
</div>
<table>
  <thead><tr><th>Description 項目</th><th>Category 類別</th><th class="r">Amount 金額</th></tr></thead>
  <tbody><tr><td>{esc(summ.split('，')[0] if summ else desc)}</td><td>{esc(desc)}</td><td class="r">{money(cur, inv.get('amt'))}</td></tr></tbody>
</table>
<div class="tot"><div class="t">
  <div class="row"><span>Subtotal 小計</span><span>{money(cur, inv.get('amt'))}</span></div>
  <div class="row"><span>GST/VAT</span><span>— (香港不征)</span></div>
  <div class="row grand"><span>Total 合計</span><span>{money(cur, inv.get('amt'))}</span></div>
</div></div>
<div class="note"><b>備註 Remarks:</b> {esc(inv.get('note',''))}<div class="gst">本發票金額以 {cur} 計價。香港不徵收增值稅/商品及服務稅 (GST/VAT)。</div></div>
<div class="foot">This is a computer-generated document for TESTING purposes only · 测试样张 · {esc(inv.get('id'))}</div>
</body></html>"""

def receipt_html(inv):
    cur = inv.get("currency", "HKD")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Courier New','PingFang HK',monospace;background:#fff;width:400px;padding:26px 24px;color:#111}}
.c{{text-align:center}}
.shop{{font-size:17px;font-weight:800}}
.sub{{font-size:11px;color:#555;margin-top:3px}}
.dash{{border-top:1px dashed #999;margin:12px 0}}
.row{{display:flex;justify-content:space-between;font-size:12.5px;margin:5px 0}}
.item{{font-size:13px;margin:8px 0}}
.tot{{font-size:16px;font-weight:800;display:flex;justify-content:space-between;margin-top:8px}}
.foot{{text-align:center;font-size:10.5px;color:#888;margin-top:16px;line-height:1.8}}
</style></head><body>
<div class="c"><div class="shop">{esc(inv['merchant'])}</div><div class="sub">{esc(inv.get('counterparty',''))}</div>
<div class="sub">BR: {esc(inv.get('br_no'))} · Hong Kong</div></div>
<div class="dash"></div>
<div class="row"><span>收據編號 No.</span><span>{esc(inv.get('invoice_no'))}</span></div>
<div class="row"><span>日期 Date</span><span>{esc(inv.get('invoice_date'))}</span></div>
<div class="row"><span>付款方式</span><span>現金 CASH</span></div>
<div class="dash"></div>
<div class="item">{esc(inv.get('category'))}</div>
<div class="row"><span>數量 x1</span><span>{money(cur, inv.get('amt'))}</span></div>
<div class="dash"></div>
<div class="tot"><span>合計 TOTAL</span><span>{money(cur, inv.get('amt'))}</span></div>
<div class="foot">多謝惠顧 Thank You<br>香港不徵 GST/VAT<br>TESTING SAMPLE · {esc(inv.get('id'))}</div>
</body></html>"""

def render(inv):
    is_receipt = inv["id"] in RECEIPT_IDS
    html_str = receipt_html(inv) if is_receipt else invoice_html(inv)
    size = "440,700" if is_receipt else "900,860"
    safe_no = str(inv.get("invoice_no","")).replace("/", "-")
    base = f"{inv['id']}_{safe_no}"
    htmlf = os.path.join(tempfile.gettempdir(), base + ".html")
    pngf  = os.path.join(OUT, base + ".png")
    with open(htmlf, "w", encoding="utf-8") as f: f.write(html_str)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--default-background-color=FFFFFFFF",
                    f"--window-size={size}", f"--screenshot={pngf}", "file://" + htmlf],
                   capture_output=True, timeout=60)
    return pngf if os.path.exists(pngf) else None

def main():
    data = json.load(open(DATA, encoding="utf-8"))
    ok = 0
    for inv in data["invoices"]:
        if inv.get("is_duplicate"):  # 重复票据不单独出图（与原票同图）
            continue
        p = render(inv)
        if p: ok += 1; print("✓", os.path.basename(p))
        else: print("✗ failed:", inv["id"])
    print(f"\n生成 {ok} 张票据图片 -> {OUT}")

if __name__ == "__main__":
    main()
