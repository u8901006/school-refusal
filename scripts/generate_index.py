#!/usr/bin/env python3
"""Generate index.html listing all School Refusal daily reports."""

import glob
import os
from datetime import datetime

html_files = sorted(glob.glob("docs/school-refusal-*.html"), reverse=True)
links = ""
for f in html_files[:30]:
    name = os.path.basename(f)
    date = name.replace("school-refusal-", "").replace(".html", "")
    try:
        d = datetime.strptime(date, "%Y-%m-%d")
        date_display = d.strftime("%Y年%-m月%-d日")
    except Exception:
        date_display = date
    weekday = (
        ["一", "二", "三", "四", "五", "六", "日"][
            datetime.strptime(date, "%Y-%m-%d").weekday()
        ]
        if len(date) == 10
        else ""
    )
    links += f'<li><a href="{name}">\U0001f4c5 {date_display}\uff08\u9031{weekday}\uff09</a></li>\n'

total = len(html_files)

index = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>School Refusal Brain \u00b7 \u62d2\u5b78/\u61fc\u5b78\u6587\u737b\u65e5\u5831</title>
<style>
  :root {{ --bg: #070b14; --surface: #0d1525; --line: #1a2744; --text: #E8EDF5; --muted: #8899B4; --accent: #7C6BFF; --accent-soft: rgba(124,107,255,0.12); }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, "PingFang TC", "Helvetica Neue", Arial, sans-serif; min-height: 100vh; }}
  .container {{ position: relative; z-index: 1; max-width: 640px; margin: 0 auto; padding: 80px 24px; }}
  .logo {{ font-size: 48px; text-align: center; margin-bottom: 16px; }}
  h1 {{ text-align: center; font-size: 24px; color: #fff; margin-bottom: 8px; }}
  .subtitle {{ text-align: center; color: #7C6BFF; font-size: 14px; margin-bottom: 48px; }}
  .count {{ text-align: center; color: var(--muted); font-size: 13px; margin-bottom: 32px; }}
  ul {{ list-style: none; }}
  li {{ margin-bottom: 8px; }}
  a {{ color: var(--text); text-decoration: none; display: block; padding: 14px 20px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; transition: all 0.2s; font-size: 15px; }}
  a:hover {{ background: rgba(124,107,255,0.05); border-color: rgba(124,107,255,0.2); transform: translateX(4px); }}
  .clinic-banner {{ margin-top: 48px; text-align: center; }}
  .clinic-link {{ display: inline-flex; align-items: center; gap: 10px; padding: 12px 20px; background: rgba(124,107,255,0.05); border: 1px solid rgba(124,107,255,0.15); border-radius: 12px; text-decoration: none; color: var(--text); transition: all 0.2s; }}
  .clinic-link:hover {{ border-color: #7C6BFF; transform: translateY(-2px); }}
  footer {{ margin-top: 32px; text-align: center; font-size: 12px; color: #37474F; }}
  footer a {{ display: inline; padding: 0; background: none; border: none; color: #546E7A; }}
  footer a:hover {{ color: #7C6BFF; }}
</style>
</head>
<body>
<div class="container">
  <div class="logo">\U0001f3eb</div>
  <h1>School Refusal Brain</h1>
  <p class="subtitle">\u62d2\u5b78/\u61fc\u5b78\u6587\u737b\u65e5\u5831 \u00b7 \u6bcf\u65e5\u81ea\u52d5\u66f4\u65b0</p>
  <p class="count">\u5171 {total} \u671f\u65e5\u5831</p>
  <ul>{links}</ul>
  <div class="clinic-banner">
    <a href="https://www.leepsyclinic.com/" class="clinic-link" target="_blank">
      <span>\U0001f3e5</span>
      <span>\u674e\u653f\u6d0b\u8eab\u5fc3\u8a3a\u6240</span>
      <span>\u2192</span>
    </a>
  </div>
  <footer>
    <p>Powered by PubMed + Zhipu AI &middot; <a href="https://github.com/u8901006/school-refusal">GitHub</a></p>
  </footer>
</div>
</body>
</html>"""

with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(index)
print("Index page generated")
