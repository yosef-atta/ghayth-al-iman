import os
import re
import sys
import shutil
import subprocess
import pathlib

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def extract_chapters_fallback_from_md(md_content):
    """Fallback: Extracts chapters and sub-axes directly from markdown if chapters.md is missing."""
    chapters = {}
    current_ch = None
    lines = md_content.splitlines()
    
    for line in lines:
        line_s = line.strip()
        if line_s.startswith('# ') and not line_s.startswith('# غيث الإيمان'):
            ch_raw = line_s[2:].strip()
            if ':' in ch_raw:
                ch_key, ch_title = ch_raw.split(':', 1)
                ch_key = ch_key.strip()
                ch_title = ch_title.strip()
            else:
                ch_key = ch_raw
                ch_title = ch_raw
                
            current_ch = ch_key
            chapters[current_ch] = {
                'title': ch_title,
                'desc': '',
                'axes': []
            }
        elif current_ch and (line_s.startswith('## ') or line_s.startswith('### ')):
            axis_title = re.sub(r'^[#\s]+', '', line_s).strip()
            # Clean up introductory numbers like "أولاً:", "الجزء الأول:"
            clean_axis = re.sub(r'^(الجزء\s+\w+:|القسم\s+\w+:|أولاً:|ثانياً:|ثالثاً:|رابعاً:|خامساً:)\s*', '', axis_title).strip()
            if clean_axis and clean_axis not in chapters[current_ch]['axes']:
                chapters[current_ch]['axes'].append(clean_axis)
                
    return chapters


def parse_chapters_md(filepath, md_fallback_content=""):
    if not os.path.exists(filepath):
        print("تنبيه: ملف chapters.md غير موجود، جاري استخراج بيانات الفصول تلقائياً من الماركداون...")
        return extract_chapters_fallback_from_md(md_fallback_content)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chapters = {}
    for block in content.split('## '):
        if not block.strip() or block.startswith('#'):
            continue
        lines = block.strip().splitlines()
        ch_name = lines[0].strip()
        
        title = ""
        desc = ""
        axes = []
        
        current_section = None
        for line in lines[1:]:
            line_s = line.strip()
            if line_s.startswith('* **العنوان:**') or line_s.startswith('- **العنوان:**'):
                title = line_s.split('**العنوان:**', 1)[1].strip()
            elif line_s.startswith('* **الوصف:**') or line_s.startswith('- **الوصف:**'):
                desc = line_s.split('**الوصف:**', 1)[1].strip()
            elif line_s.startswith('* **المحاور:**') or line_s.startswith('- **المحاور:**'):
                current_section = 'axes'
            elif line_s.startswith('* ') or line_s.startswith('- ') or line_s.startswith('  * '):
                if current_section == 'axes':
                    axis_text = re.sub(r'^[*\-\s]+', '', line_s).strip()
                    if axis_text:
                        axes.append(axis_text)
                        
        chapters[ch_name] = {
            'title': title,
            'desc': desc,
            'axes': axes
        }
    return chapters


def format_inline_markdown(text):
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    text = re.sub(r'\_(.*?)\_', r'<em>\1</em>', text)
    text = re.sub(r'﴿(.*?)﴾', r'<span class="quran-text">﴿\1﴾</span>', text)
    text = re.sub(r'«(.*?)»', r'<span class="hadith-text">«\1»</span>', text)
    return text


def build_html():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(base_dir, 'غيث-الإيمان.md')
    chapters_path = os.path.join(base_dir, 'chapters.md')
    cover_path = os.path.join(base_dir, 'cover.png')
    
    # Fallback if master markdown is missing: compile from individual chapters
    if not os.path.exists(md_path):
        print("تنبيه: ملف غيث-الإيمان.md غير موجود، جاري بناؤه تلقائياً من ملفات الفصول...")
        try:
            import generator_md
            generator_md.generate_master_markdown('غيث-الإيمان.md')
        except Exception as e:
            print(f"فشل تشغيل generator_md: {e}")
            
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    chapters_meta = parse_chapters_md(chapters_path, md_content)

    lines = md_content.splitlines()
    body_html = []
    
    # 1. Cover Page (With Fallback if cover.png is missing)
    if os.path.exists(cover_path):
        cover_html = f'''
        <div class="cover-page">
            <img src="{cover_path.replace(os.sep, '/')}" class="cover-img" alt="غلاف غيث الإيمان">
        </div>
        '''
    else:
        print("تنبيه: ملف cover.png غير موجود، سيتم توليد غلاف بديل فخم تلقائياً عبر CSS.")
        cover_html = '''
        <div class="cover-page cover-fallback">
            <div class="cover-fallback-border">
                <div class="cover-fallback-badge">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>
                <h1 class="cover-fallback-title">غَيْثُ الإِيمَان</h1>
                <div class="cover-fallback-subtitle">رحلة العقل والمنطق من العدم إلى اليقين</div>
                <div class="cover-fallback-divider">❖ ❖ ❖</div>
                <div class="cover-fallback-footer">إصدار إلكتروني موثق</div>
            </div>
        </div>
        '''
    
    # 2. Table of Contents Generation
    toc_html = ['<div class="page toc-page">']
    toc_html.append('<div class="toc-header">')
    toc_html.append('<div class="toc-bismillah">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>')
    toc_html.append('<h2 class="toc-main-title">فهرس فصول الكتاب</h2>')
    toc_html.append('<div class="toc-decorative-line">❖ ❖ ❖</div>')
    toc_html.append('</div>')
    toc_html.append('<div class="toc-list">')
    
    for ch_name, data in chapters_meta.items():
        toc_html.append('<div class="toc-item">')
        toc_html.append(f'<div class="toc-item-header"><span class="toc-ch-num">{ch_name}</span><span class="toc-ch-title">{data["title"]}</span></div>')
        if data["desc"]:
            toc_html.append(f'<div class="toc-item-desc">{data["desc"]}</div>')
        if data["axes"]:
            toc_html.append('<div class="toc-item-axes">')
            for ax in data["axes"][:5]: # display up to 5 axes in TOC
                toc_html.append(f'<span class="toc-axis-tag">• {ax}</span>')
            toc_html.append('</div>')
        toc_html.append('</div>')
        
    toc_html.append('</div>')
    toc_html.append('</div>') # end toc-page
    
    # 3. Parse Markdown Lines into Clean Balanced HTML
    i = 0
    total_lines = len(lines)
    seen_first_chapter = False
    current_list_type = None # 'ul' or 'ol'
    
    def close_list():
        nonlocal current_list_type
        res = ''
        if current_list_type:
            res = f'</{current_list_type}>\n'
            current_list_type = None
        return res

    while i < total_lines:
        line_raw = lines[i]
        line_s = line_raw.strip()
        
        # Skip top-level main book title
        if line_s.startswith('# غيث الإيمان:'):
            i += 1
            continue
            
        # Empty line
        if not line_s:
            if current_list_type:
                body_html.append(close_list())
            i += 1
            continue

        # Horizontal rule
        if line_s in ['---', '***', '___']:
            if current_list_type:
                body_html.append(close_list())
            next_is_chapter = False
            for j in range(i + 1, min(i + 10, total_lines)):
                nl = lines[j].strip()
                if nl:
                    if nl.startswith('# '):
                        next_is_chapter = True
                    break
            if seen_first_chapter and not next_is_chapter:
                body_html.append('<div class="section-divider">❖ ❖ ❖</div>\n')
            i += 1
            continue

        # Chapter Heading (H1)
        if line_s.startswith('# '):
            seen_first_chapter = True
            if current_list_type:
                body_html.append(close_list())
            ch_raw = line_s[2:].strip()
            ch_key = ch_raw.split(':', 1)[0].strip()
            ch_info = chapters_meta.get(ch_key, None)
            
            body_html.append('<div class="chapter-start">\n')
            if ch_info:
                body_html.append('<div class="chapter-opener-card">\n')
                body_html.append(f'  <div class="ch-badge">{ch_key}</div>\n')
                body_html.append(f'  <h1 class="chapter-title">{ch_info["title"]}</h1>\n')
                if ch_info["desc"]:
                    body_html.append(f'  <p class="ch-desc">{ch_info["desc"]}</p>\n')
                if ch_info["axes"]:
                    body_html.append('  <div class="ch-axes-box">\n')
                    body_html.append('    <div class="ch-axes-title">📌 محاور الفصل:</div>\n')
                    body_html.append('    <ul class="ch-axes-list">\n')
                    for ax in ch_info["axes"]:
                        body_html.append(f'      <li>{ax}</li>\n')
                    body_html.append('    </ul>\n  </div>\n')
                body_html.append('</div>\n')
            else:
                body_html.append(f'<h1 class="chapter-title">{ch_raw}</h1>\n')
            body_html.append('</div>\n')
            i += 1
            continue

        # Section Heading (H2)
        if line_s.startswith('## '):
            if current_list_type:
                body_html.append(close_list())
            h2_text = format_inline_markdown(line_s[3:].strip())
            body_html.append(f'<h2 class="section-title">{h2_text}</h2>\n')
            i += 1
            continue

        # Subsection Heading (H3)
        if line_s.startswith('### '):
            if current_list_type:
                body_html.append(close_list())
            h3_text = format_inline_markdown(line_s[4:].strip())
            body_html.append(f'<h3 class="subsection-title">{h3_text}</h3>\n')
            i += 1
            continue

        # Sub-subsection Heading (H4)
        if line_s.startswith('#### '):
            if current_list_type:
                body_html.append(close_list())
            h4_raw = line_s[5:].strip()
            badge_html = ""
            if '(نخبوي - الضربة القاضية)' in h4_raw:
                badge_html = '<span class="badge badge-knockout">نخبوي - الضربة القاضية ⚡</span>'
                h4_raw = h4_raw.replace('(نخبوي - الضربة القاضية)', '').strip()
            elif '(نخبوي)' in h4_raw:
                badge_html = '<span class="badge badge-elite">نخبوي 🎯</span>'
                h4_raw = h4_raw.replace('(نخبوي)', '').strip()
            elif '(شائع)' in h4_raw:
                badge_html = '<span class="badge badge-common">شائع 💡</span>'
                h4_raw = h4_raw.replace('(شائع)', '').strip()
            h4_text = format_inline_markdown(h4_raw)
            body_html.append(f'<h4 class="claim-heading"><span class="heading-text">{h4_text}</span> {badge_html}</h4>\n')
            i += 1
            continue

        # Question Bullet: * **السؤال X:**
        if re.match(r'^[*\-]\s+\*\*السؤال\s+\d+:\*\*', line_s):
            if current_list_type:
                body_html.append(close_list())
            q_match = re.match(r'^[*\-]\s+\*\*(السؤال\s+\d+:)\*\*(.*)', line_s)
            q_num = q_match.group(1).strip()
            q_body = format_inline_markdown(q_match.group(2).strip())
            body_html.append(f'<div class="question-card"><div class="q-header"><span class="q-icon">❓</span> <span class="q-num">{q_num}</span></div><div class="q-text">{q_body}</div></div>\n')
            i += 1
            continue

        # Claim / Excuse: * **مبرر الملحد:**
        if re.match(r'^[*\-]\s+\*\*(مبرر الملحد|المبرر|الشبهة|مبرر الشبهة):\*\*', line_s):
            if current_list_type:
                body_html.append(close_list())
            c_match = re.match(r'^[*\-]\s+\*\*(مبرر الملحد|المبرر|الشبهة|مبرر الشبهة):\*\*(.*)', line_s)
            c_title = c_match.group(1).strip()
            c_body = format_inline_markdown(c_match.group(2).strip())
            body_html.append(f'<div class="claim-card"><div class="card-header claim-header"><span class="card-icon">🗣️</span> <span class="card-title">{c_title}:</span></div><div class="card-body claim-body">{c_body}</div></div>\n')
            i += 1
            continue

        # Rebuttal: * **المغالطة:** or * **الرد:**
        if re.match(r'^[*\-]\s+\*\*(المغالطة|الرد|تفكيك المغالطة|الرد المنطقي):\*\*', line_s):
            if current_list_type:
                body_html.append(close_list())
            r_match = re.match(r'^[*\-]\s+\*\*(المغالطة|الرد|تفكيك المغالطة|الرد المنطقي):\*\*(.*)', line_s)
            r_title = r_match.group(1).strip()
            first_p = r_match.group(2).strip()
            
            rebuttal_lines = [first_p] if first_p else []
            
            while i + 1 < total_lines:
                next_l = lines[i + 1].strip()
                if not next_l:
                    if i + 2 < total_lines and (lines[i+2].startswith('  ') or lines[i+2].startswith('\t')):
                        i += 1
                        continue
                    else:
                        break
                if next_l.startswith(('#', '---', '***', '___')):
                    break
                if re.match(r'^[*\-]\s+\*\*(السؤال|مبرر|المبرر|الشبهة|المغالطة|الرد)', next_l):
                    break
                i += 1
                rebuttal_lines.append(next_l)
                
            reb_html_parts = []
            for r_line in rebuttal_lines:
                if r_line.startswith('> '):
                    reb_html_parts.append(f'<div class="inner-quote">{format_inline_markdown(r_line[2:].strip())}</div>')
                elif re.match(r'^\d+\.\s+\*\*', r_line):
                    reb_html_parts.append(f'<div class="sub-point-item">{format_inline_markdown(r_line)}</div>')
                elif r_line.startswith('* ') or r_line.startswith('- '):
                    reb_html_parts.append(f'<div class="sub-bullet-item">{format_inline_markdown(r_line[2:].strip())}</div>')
                else:
                    reb_html_parts.append(f'<p class="card-para">{format_inline_markdown(r_line)}</p>')
                    
            r_body_html = ''.join(reb_html_parts)
            body_html.append(f'<div class="rebuttal-card"><div class="card-header rebuttal-header"><span class="card-icon">🛡️</span> <span class="card-title">{r_title}:</span></div><div class="card-body rebuttal-body">{r_body_html}</div></div>\n')
            i += 1
            continue

        # Blockquote / Quran / Hadith / Quote
        if line_s.startswith('> '):
            if current_list_type:
                body_html.append(close_list())
            q_text = line_s[2:].strip()
            while i + 1 < total_lines and lines[i+1].strip().startswith('> '):
                i += 1
                q_text += '<br>' + lines[i].strip()[2:].strip()
            f_quote = format_inline_markdown(q_text)
            if '﴿' in q_text or 'تعالى' in q_text:
                body_html.append(f'<div class="quran-card"><div class="quran-badge">📖 آية كريمة</div><div class="quran-content">{f_quote}</div></div>\n')
            elif 'رسول الله' in q_text or 'النبي' in q_text or 'ﷺ' in q_text:
                body_html.append(f'<div class="hadith-card"><div class="hadith-badge">✨ حديث شريف</div><div class="hadith-content">{f_quote}</div></div>\n')
            else:
                body_html.append(f'<div class="quote-card"><div class="quote-content">{f_quote}</div></div>\n')
            i += 1
            continue

        # Regular Unordered List Item
        if line_s.startswith('* ') or line_s.startswith('- '):
            if current_list_type != 'ul':
                if current_list_type:
                    body_html.append(close_list())
                body_html.append('<ul class="regular-list">\n')
                current_list_type = 'ul'
            item_text = format_inline_markdown(line_s[2:].strip())
            body_html.append(f'  <li>{item_text}</li>\n')
            i += 1
            continue

        # Regular Ordered List Item
        if re.match(r'^\d+\.\s+', line_s):
            if current_list_type != 'ol':
                if current_list_type:
                    body_html.append(close_list())
                body_html.append('<ol class="regular-list">\n')
                current_list_type = 'ol'
            num_match = re.match(r'^\d+\.\s+(.*)', line_s)
            item_text = format_inline_markdown(num_match.group(1).strip())
            body_html.append(f'  <li>{item_text}</li>\n')
            i += 1
            continue

        # Regular Paragraph
        if current_list_type:
            body_html.append(close_list())
            
        p_formatted = format_inline_markdown(line_s)
        if '﴿' in line_s and '﴾' in line_s and len(line_s) < 250:
            body_html.append(f'<div class="quran-card"><div class="quran-badge">📖 آية كريمة</div><div class="quran-content">{p_formatted}</div></div>\n')
        elif ('قال رسول الله' in line_s or 'قال النبي' in line_s) and len(line_s) < 300:
            body_html.append(f'<div class="hadith-card"><div class="hadith-badge">✨ حديث شريف</div><div class="hadith-content">{p_formatted}</div></div>\n')
        else:
            body_html.append(f'<p class="body-text">{p_formatted}</p>\n')
        i += 1

    if current_list_type:
        body_html.append(close_list())

    # Complete HTML Document
    html_template = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>غيث الإيمان</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400;1,700&family=Aref+Ruqaa:wght@400;700&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: A4 portrait;
            margin: 20mm 18mm 22mm 18mm;
            @bottom-center {{
                content: counter(page);
                font-family: 'Amiri', serif;
                font-size: 11pt;
                color: #718096;
            }}
        }}

        @page :first {{
            margin: 0;
            @bottom-center {{
                content: normal;
            }}
        }}

        * {{
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}

        body {{
            font-family: 'Amiri', serif;
            font-size: 14pt;
            line-height: 1.85;
            color: #1a202c;
            background-color: #ffffff;
            margin: 0;
            padding: 0;
            direction: rtl;
            text-align: justify;
            text-justify: inter-word;
            orphans: 3;
            widows: 3;
        }}

        /* Cover Page */
        .cover-page {{
            width: 100vw;
            height: 100vh;
            page-break-after: always;
            page-break-inside: avoid;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #ffffff;
        }}

        .cover-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}

        /* Cover Fallback (if cover.png is missing) */
        .cover-fallback {{
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            color: #ffffff;
            padding: 40px;
        }}

        .cover-fallback-border {{
            border: 3px double #fbbf24;
            border-radius: 16px;
            width: 90%;
            height: 90%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 40px 20px;
            background: rgba(15, 23, 42, 0.4);
            box-shadow: inset 0 0 30px rgba(0,0,0,0.5);
        }}

        .cover-fallback-badge {{
            font-family: 'Amiri', serif;
            font-size: 18pt;
            color: #fbbf24;
            margin-bottom: 30px;
        }}

        .cover-fallback-title {{
            font-family: 'Aref Ruqaa', serif;
            font-size: 42pt;
            color: #ffffff;
            margin: 10px 0 20px 0;
            text-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }}

        .cover-fallback-subtitle {{
            font-family: 'Amiri', serif;
            font-size: 18pt;
            color: #93c5fd;
            max-width: 80%;
            line-height: 1.6;
            margin-bottom: 30px;
        }}

        .cover-fallback-divider {{
            color: #fbbf24;
            font-size: 16pt;
            letter-spacing: 8px;
            margin-bottom: 30px;
        }}

        .cover-fallback-footer {{
            font-family: 'Amiri', serif;
            font-size: 14pt;
            color: #cbd5e1;
        }}

        /* Table of Contents Page */
        .toc-page {{
            page-break-before: always;
            page-break-after: always;
            page-break-inside: avoid;
            padding-top: 5px;
        }}

        .toc-header {{
            text-align: center;
            margin-bottom: 12px;
        }}

        .toc-bismillah {{
            font-family: 'Amiri', serif;
            font-size: 14pt;
            color: #065f46;
            margin-bottom: 2px;
        }}

        .toc-main-title {{
            font-family: 'Aref Ruqaa', serif;
            font-size: 22pt;
            font-weight: 700;
            color: #0f2942;
            margin: 2px 0;
        }}

        .toc-decorative-line {{
            color: #d97706;
            font-size: 11pt;
            letter-spacing: 4px;
        }}

        .toc-list {{
            display: flex;
            flex-direction: column;
            gap: 9px;
        }}

        .toc-item {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-right: 4px solid #1e3a8a;
            border-radius: 8px;
            padding: 8px 14px;
        }}

        .toc-item-header {{
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 4px;
        }}

        .toc-ch-num {{
            font-family: 'Aref Ruqaa', serif;
            font-size: 13.5pt;
            font-weight: bold;
            color: #1e3a8a;
            background: #e0e7ff;
            padding: 1px 8px;
            border-radius: 5px;
        }}

        .toc-ch-title {{
            font-family: 'Aref Ruqaa', serif;
            font-size: 14.5pt;
            font-weight: bold;
            color: #0f2942;
        }}

        .toc-item-desc {{
            font-size: 11pt;
            line-height: 1.5;
            color: #475569;
            margin-bottom: 5px;
        }}

        .toc-item-axes {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}

        .toc-axis-tag {{
            font-size: 9.5pt;
            background: #edf2f7;
            color: #2b6cb0;
            padding: 1px 6px;
            border-radius: 4px;
            border: 1px solid #cbd5e1;
        }}

        /* Chapter Start & Opener Card */
        .chapter-start {{
            page-break-before: always;
            margin-top: 10px;
            margin-bottom: 20px;
        }}

        .chapter-opener-card {{
            background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
            border: 1.5px solid #bfdbfe;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 4px 10px rgba(30, 58, 138, 0.05);
            margin-bottom: 20px;
            page-break-inside: avoid;
        }}

        .ch-badge {{
            display: inline-block;
            font-family: 'Aref Ruqaa', serif;
            font-size: 13pt;
            font-weight: bold;
            background: #1e3a8a;
            color: #ffffff;
            padding: 2px 14px;
            border-radius: 16px;
            margin-bottom: 8px;
        }}

        .chapter-title {{
            font-family: 'Aref Ruqaa', serif;
            font-size: 21pt;
            font-weight: 700;
            color: #0f2942;
            margin: 0 0 8px 0;
            line-height: 1.35;
        }}

        .ch-desc {{
            font-size: 12.5pt;
            line-height: 1.65;
            color: #334155;
            margin: 0 0 12px 0;
            border-right: 3px solid #60a5fa;
            padding-right: 10px;
        }}

        .ch-axes-box {{
            background: #ffffff;
            border: 1px dashed #93c5fd;
            border-radius: 7px;
            padding: 8px 12px;
        }}

        .ch-axes-title {{
            font-weight: bold;
            font-size: 11.5pt;
            color: #1e3a8a;
            margin-bottom: 4px;
        }}

        .ch-axes-list {{
            margin: 0;
            padding-right: 18px;
            font-size: 11pt;
            color: #475569;
            line-height: 1.55;
        }}

        /* Headings */
        .section-title {{
            font-family: 'Aref Ruqaa', serif;
            font-size: 18pt;
            font-weight: 700;
            color: #1e3a8a;
            margin-top: 24px;
            margin-bottom: 12px;
            border-bottom: 2px solid #dbeafe;
            padding-bottom: 5px;
            page-break-after: avoid;
        }}

        .subsection-title {{
            font-family: 'Amiri', serif;
            font-size: 15.5pt;
            font-weight: 700;
            color: #2b6cb0;
            margin-top: 18px;
            margin-bottom: 10px;
            page-break-after: avoid;
        }}

        .claim-heading {{
            font-family: 'Amiri', serif;
            font-size: 14.5pt;
            font-weight: 700;
            color: #1a365d;
            margin-top: 18px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
            background: #f8fafc;
            border-right: 4px solid #3b82f6;
            padding: 6px 12px;
            border-radius: 6px;
            page-break-after: avoid;
        }}

        .heading-text {{
            flex: 1;
        }}

        /* Badges */
        .badge {{
            font-family: 'Amiri', serif;
            font-size: 10.5pt;
            font-weight: bold;
            padding: 2px 9px;
            border-radius: 12px;
            display: inline-block;
        }}

        .badge-elite {{
            background-color: #fff5f5;
            color: #c53030;
            border: 1px solid #feb2b2;
        }}

        .badge-common {{
            background-color: #f0fff4;
            color: #276749;
            border: 1px solid #9ae6b4;
        }}

        .badge-knockout {{
            background-color: #fef2f2;
            color: #991b1b;
            border: 1.5px solid #f87171;
            box-shadow: 0 1px 3px rgba(239, 68, 68, 0.15);
        }}

        /* Question Card */
        .question-card {{
            background: #f0f7ff;
            border: 1.5px solid #bae6fd;
            border-radius: 8px;
            padding: 10px 14px;
            page-break-inside: avoid;
            margin: 10px 0;
        }}

        .q-header {{
            font-weight: bold;
            color: #0369a1;
            font-size: 13.5pt;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .q-text {{
            color: #1e293b;
            font-size: 13.5pt;
            line-height: 1.7;
        }}

        /* Claim Card */
        .claim-card {{
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-right: 4px solid #64748b;
            border-radius: 8px;
            padding: 10px 14px;
            page-break-inside: avoid;
            margin: 10px 0;
        }}

        .claim-header {{
            font-weight: bold;
            color: #334155;
            font-size: 13.5pt;
            margin-bottom: 4px;
        }}

        .claim-body {{
            color: #1e293b;
            font-size: 13.5pt;
            line-height: 1.7;
        }}

        /* Rebuttal Card */
        .rebuttal-card {{
            background: #ffffff;
            border: 1.5px solid #cbd5e1;
            border-right: 4px solid #059669;
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.02);
            page-break-inside: avoid;
            margin: 12px 0;
        }}

        .rebuttal-header {{
            font-weight: bold;
            color: #047857;
            font-size: 14pt;
            margin-bottom: 6px;
        }}

        .rebuttal-body {{
            color: #1a202c;
            font-size: 13.5pt;
            line-height: 1.75;
        }}

        .card-para {{
            margin: 6px 0;
            line-height: 1.75;
        }}

        .sub-point-item {{
            margin: 8px 0 6px 0;
            padding-right: 10px;
            border-right: 2.5px solid #86efac;
            font-size: 13pt;
            line-height: 1.65;
        }}

        .sub-bullet-item {{
            margin: 4px 0;
            padding-right: 14px;
            position: relative;
            font-size: 13pt;
            line-height: 1.65;
        }}
        .sub-bullet-item::before {{
            content: "•";
            color: #059669;
            position: absolute;
            right: 2px;
            font-weight: bold;
        }}

        .inner-quote {{
            background: #f8fafc;
            border-right: 3px solid #64748b;
            padding: 6px 12px;
            margin: 8px 0;
            border-radius: 4px;
            font-style: italic;
            color: #334155;
            font-size: 13pt;
        }}

        .card-icon {{
            margin-left: 4px;
        }}

        /* Quran & Hadith Cards */
        .quran-card {{
            background: #f0fdf4;
            border: 1.5px solid #86efac;
            border-radius: 10px;
            padding: 12px 18px;
            margin: 14px 0;
            text-align: center;
            page-break-inside: avoid;
        }}

        .quran-badge {{
            font-size: 10.5pt;
            font-weight: bold;
            color: #15803d;
            margin-bottom: 4px;
        }}

        .quran-content, .quran-text {{
            font-family: 'Amiri', serif;
            font-weight: bold;
            font-size: 15pt;
            color: #065f46;
            line-height: 2.0;
        }}

        .hadith-card {{
            background: #fffbeb;
            border: 1.5px solid #fde68a;
            border-radius: 10px;
            padding: 12px 18px;
            margin: 14px 0;
            text-align: center;
            page-break-inside: avoid;
        }}

        .hadith-badge {{
            font-size: 10.5pt;
            font-weight: bold;
            color: #b45309;
            margin-bottom: 4px;
        }}

        .hadith-content, .hadith-text {{
            font-family: 'Amiri', serif;
            font-weight: bold;
            font-size: 14.5pt;
            color: #854d0e;
            line-height: 1.9;
        }}

        /* Quotes */
        .quote-card {{
            background: #f8fafc;
            border-right: 4px solid #4a5568;
            border-radius: 0 8px 8px 0;
            padding: 10px 16px;
            margin: 12px 0;
            font-style: italic;
            color: #4a5568;
            page-break-inside: avoid;
        }}

        /* General Typography */
        p.body-text {{
            margin: 8px 0;
            line-height: 1.8;
            font-size: 14pt;
        }}

        .regular-list {{
            margin: 8px 0;
            padding-right: 22px;
            font-size: 13.5pt;
            line-height: 1.75;
        }}

        .section-divider {{
            text-align: center;
            color: #94a3b8;
            font-size: 13pt;
            letter-spacing: 5px;
            margin: 20px 0;
            page-break-after: avoid;
        }}

        @media print {{
            body {{
                width: 100%;
            }}
            .cover-page {{
                page-break-after: always;
            }}
            .toc-page {{
                page-break-after: always;
            }}
            .chapter-start {{
                page-break-before: always;
            }}
        }}
    </style>
</head>
<body>

    <!-- Cover Page (Image or Fallback) -->
    {cover_html}

    <!-- Table of Contents -->
    {''.join(toc_html)}

    <!-- Main Content -->
    {''.join(body_html)}

</body>
</html>
'''
    html_file = os.path.join(base_dir, 'book.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    print(f"Generated HTML at: {html_file}")
    return html_file


def generate_pdf():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = build_html()
    pdf_file = os.path.join(base_dir, 'غيث-الإيمان.pdf')
    
    edge_paths = [
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        shutil.which('msedge') or '',
        shutil.which('chrome') or ''
    ]
    
    browser_exe = None
    for p in edge_paths:
        if p and os.path.exists(p):
            browser_exe = p
            break
            
    if not browser_exe:
        print("Error: Could not find Microsoft Edge or Chrome executable.")
        return False

    print(f"Found browser executable: {browser_exe}")
    print(f"Rendering PDF to: {pdf_file}...")

    file_uri = pathlib.Path(html_file).absolute().as_uri()

    cmd = [
        browser_exe,
        '--headless',
        '--disable-gpu',
        '--allow-file-access-from-files',
        '--enable-local-file-accesses',
        '--no-pdf-header-footer',
        '--virtual-time-budget=5000',
        '--run-all-compositor-stages-before-draw',
        f'--print-to-pdf={pdf_file}',
        file_uri
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 1000:
        print(f"SUCCESS! Generated PDF ({os.path.getsize(pdf_file)} bytes) successfully.")
        return True
    else:
        print(f"PDF generation failed: {result.stderr}")
        return False


if __name__ == '__main__':
    generate_pdf()
