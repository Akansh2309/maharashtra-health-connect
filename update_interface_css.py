import re

with open('public/interface.html', 'r') as f:
    html = f.read()

new_css = """
        :root {
            --primary-color: #0056b3;
            --primary-hover: #004494;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #333333;
            --text-muted: #666666;
            --border-color: #cbd5e1;
            --error-color: #dc2626;
            --success-color: #15803d;
            --focus-ring: #93c5fd;
            --input-bg: #ffffff;
            --fieldset-bg: #fafafa;
        }
        :root[data-theme="dark"] {
            --primary-color: #3b82f6;
            --primary-hover: #60a5fa;
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --input-bg: #0f172a;
            --fieldset-bg: transparent;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background-color: var(--bg-color); color: var(--text-main); line-height: 1.5; min-height: 100vh; display: flex; flex-direction: column; }
        header { background-color: var(--card-bg); border-bottom: 1px solid var(--border-color); padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; }
        .brand-title { font-size: 1.25rem; font-weight: 700; color: var(--primary-color); }
        .brand-subtitle { font-size: 0.85rem; color: var(--text-muted); }
        main { flex: 1; padding: 20px 16px; display: flex; justify-content: center; align-items: flex-start; }
        .auth-container { background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); width: 100%; max-width: 500px; padding: 24px; color: var(--text-main); }
        .auth-header { text-align: center; margin-bottom: 24px; }
        .auth-header h1 { font-size: 1.5rem; color: var(--primary-color); margin-bottom: 8px; }
        .tabs { display: flex; border-bottom: 1px solid var(--border-color); margin-bottom: 20px; }
        .tab-btn { flex: 1; padding: 12px; background: none; border: none; border-bottom: 3px solid transparent; font-size: 1rem; font-weight: 600; color: var(--text-muted); cursor: pointer; }
        .tab-btn.active { color: var(--primary-color); border-bottom-color: var(--primary-color); }
        .form-section { display: none; }
        .form-section.active { display: block; }
        fieldset { border: 1px solid var(--border-color); border-radius: 6px; padding: 16px; margin-bottom: 20px; background-color: var(--fieldset-bg); }
        legend { font-weight: 600; padding: 0 8px; background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 4px; color: var(--text-main); }
        .form-group { margin-bottom: 16px; }
        label { display: block; margin-bottom: 6px; font-weight: 500; font-size: 0.95rem; color: var(--text-main); }
        .required { color: var(--error-color); }
        input[type="text"], input[type="tel"], input[type="email"], input[type="password"], input[type="date"], select.form-control { width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: 4px; font-size: 1rem; background-color: var(--input-bg); color: var(--text-main); }
        input::placeholder { color: var(--text-muted); }
"""

html = re.sub(r':root\s*\{.*?(?=\.radio-group \{)', new_css, html, flags=re.DOTALL)

with open('public/interface.html', 'w') as f:
    f.write(html)
