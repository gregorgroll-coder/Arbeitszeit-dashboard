import os
import json
import re
from datetime import datetime
from collections import defaultdict

def parse_markdown_log(filepath):
    daily_data = {}
    global_total_minutes = 0
    
    if not os.path.exists(filepath):
        print(f"Fehler: Die Datei {filepath} wurde nicht gefunden.")
        return None, 0

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line.startswith('|') or 'Datum' in line or '---' in line:
            continue
        
        parts = [p.strip() for p in line.split('|')][1:-1]
        if len(parts) >= 5:
            date_str, start, end, category = parts[:4]
            desc = parts[4]
            
            # Markdown Bilder umwandeln
            desc_html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" class="log-img" title="Zum Vergrößern klicken">', desc)
            # Fetten Text (**Text**) umwandeln
            desc_html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: var(--text-main); font-size: 12.5px;">\1</strong>', desc_html)
            # Kursiven Text (*Text*) umwandeln
            desc_html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', desc_html)
            
            try:
                t1 = datetime.strptime(start, "%H:%M")
                t2 = datetime.strptime(end, "%H:%M")
                delta_minutes = (t2 - t1).total_seconds() / 60
                
                if delta_minutes < 0: delta_minutes += 24 * 60 
                global_total_minutes += delta_minutes

                if date_str not in daily_data:
                    daily_data[date_str] = {"total_minutes": 0, "categories": defaultdict(int), "entries": []}
                
                daily_data[date_str]["total_minutes"] += delta_minutes
                daily_data[date_str]["categories"][category] += delta_minutes
                
                daily_data[date_str]["entries"].append({
                    "start": start, "end": end,
                    "start_min": t1.hour * 60 + t1.minute,
                    "end_min": t2.hour * 60 + t2.minute,
                    "category": category, "desc": desc_html, "duration": delta_minutes
                })
            except ValueError:
                continue

    return dict(sorted(daily_data.items())), global_total_minutes

def generate_html_dashboard(data, global_total_minutes, output_file="index.html"):
    dates = list(data.keys())
    
    json_data = json.dumps(data).replace("</", "<\\/")
    json_dates = json.dumps(dates).replace("</", "<\\/")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="Work Log">
        
        <title>Arbeitszeit Cockpit</title>
        <style>
            :root {{ 
                --text-main: #0c0d0e; 
                --text-muted: #56585d; 
                
                /* Echte Apple Glassmorphism Farbwerte */
                --glass-panel-bg: rgba(255, 255, 255, 0.42);
                --glass-card-bg: rgba(255, 255, 255, 0.38);
                --glass-border-light: rgba(255, 255, 255, 0.7);
                --glass-border-subtle: rgba(255, 255, 255, 0.4);
                --apple-blue: #0071e3;
            }}
            
            * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
            
            html, body {{
                margin: 0; padding: 0;
                min-height: 100dvh;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif;
                background-color: #0b1329;
                display: flex; justify-content: center; align-items: center;
                overflow-x: hidden;
            }}

            /* --- VIVID APPLE AMBIENT BACKGROUND GLOW --- */
            /* Diese diffusen Lichtquellen brechen sich im Glaspanel */
            .ambient-background {{
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                z-index: 0; overflow: hidden; pointer-events: none;
            }}
            .glow-orb {{
                position: absolute; border-radius: 50%; filter: blur(75px); opacity: 0.7;
                animation: floatOrb 18s ease-in-out infinite alternate;
            }}
            .orb-1 {{ width: 340px; height: 340px; background: #38bdf8; top: -50px; left: -80px; }}
            .orb-2 {{ width: 380px; height: 380px; background: #6366f1; bottom: -60px; right: -70px; animation-duration: 22s; }}
            .orb-3 {{ width: 280px; height: 280px; background: #a855f7; top: 35%; left: 25%; opacity: 0.45; }}

            @keyframes floatOrb {{
                0% {{ transform: translate(0, 0) scale(1); }}
                50% {{ transform: translate(30px, 40px) scale(1.08); }}
                100% {{ transform: translate(-20px, 25px) scale(0.95); }}
            }}

            /* --- APPLE LIQUID GLASS PANEL --- */
            .glass-panel {{
                width: 100%; height: 100dvh; 
                background: var(--glass-panel-bg); 
                /* Die magische Apple-Kombination: starker Blur + hohe Farbsättigung */
                backdrop-filter: blur(40px) saturate(190%) contrast(102%) brightness(104%);
                -webkit-backdrop-filter: blur(40px) saturate(190%) contrast(102%) brightness(104%);
                
                /* Lichtbrechende Kanten (Oben weißes Highlight, unten feiner Schatten) */
                border: 1px solid var(--glass-border-subtle);
                box-shadow: 
                    0 25px 50px rgba(0, 0, 0, 0.2),
                    inset 0 1.5px 1.5px 0 rgba(255, 255, 255, 0.75),
                    inset 0 -1px 1px 0 rgba(0, 0, 0, 0.05);

                display: flex; flex-direction: column; position: relative; overflow: hidden; 
                padding: max(env(safe-area-inset-top), 35px) 22px max(env(safe-area-inset-bottom), 20px) 22px; 
                z-index: 1;
            }}
            
            @media (min-width: 550px) {{
                .glass-panel {{
                    height: 92vh; max-width: 460px; max-height: 890px;
                    border-radius: 46px; padding: 30px 24px;
                }}
            }}
            
            /* DYNAMISCHE KOPFZEILE */
            .global-stats {{ text-align: center; margin-bottom: 16px; margin-top: 5px; flex-shrink: 0; }}
            .global-hours {{ 
                font-size: 48px; font-weight: 700; letter-spacing: -1.8px; 
                color: var(--text-main); line-height: 1; 
                transition: transform 0.2s cubic-bezier(0.25, 1, 0.5, 1);
            }}
            .global-label {{ 
                font-size: 11.5px; color: var(--text-muted); font-weight: 600; 
                margin-top: 8px; text-transform: uppercase; letter-spacing: 0.9px; 
            }}

            /* SEGMENTED CONTROL (SCHIEBER) */
            .segmented-control {{ 
                position: relative; display: flex; 
                background: rgba(0, 0, 0, 0.06); 
                border-radius: 14px; padding: 3px; margin-bottom: 18px; 
                border: 1px solid rgba(255, 255, 255, 0.35); flex-shrink: 0; 
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
                touch-action: none; cursor: pointer;
            }}
            .control-btn {{ 
                flex: 1; border: none; background: none; padding: 8px 0; 
                font-size: 13px; font-weight: 600; color: var(--text-main); 
                pointer-events: none; z-index: 2; 
            }}
            .slider-pill {{ 
                position: absolute; top: 3px; left: 3px; width: calc(33.333% - 4px); height: calc(100% - 6px); 
                background: rgba(255, 255, 255, 0.92); 
                box-shadow: 0 3px 10px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.06); 
                border-radius: 11px; z-index: 1; 
                transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1); 
            }}

            .view-container {{ flex: 1; position: relative; width: 100%; overflow: hidden; }}
            .main-view {{ 
                position: absolute; width: 100%; height: 100%; top: 0; left: 0; 
                display: flex; flex-direction: column; opacity: 0; pointer-events: none; 
                transform: scale(0.97); transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1), opacity 0.25s ease; 
            }}
            .main-view.active-view {{ opacity: 1; pointer-events: auto; transform: scale(1); }}

            /* --- DYNAMISCHE MONATS-CONTAINER (VERTIKAL WISCHBAR) --- */
            .month-scroll-container {{
                flex: 1; overflow-y: auto; overflow-x: hidden;
                -webkit-overflow-scrolling: touch;
                scroll-snap-type: y mandatory;
                padding-bottom: 40px;
                display: flex; flex-direction: column; gap: 24px;
            }}
            /* Dünne, unauffällige Scrollbar */
            .month-scroll-container::-webkit-scrollbar {{ width: 4px; }}
            .month-scroll-container::-webkit-scrollbar-thumb {{ background: rgba(0,0,0,0.15); border-radius: 4px; }}

            .month-card {{
                scroll-snap-align: center;
                flex-shrink: 0;
                background: var(--glass-card-bg);
                border-radius: 24px;
                padding: 16px;
                border: 1px solid var(--glass-border-light);
                box-shadow: 
                    0 8px 24px rgba(0,0,0,0.04),
                    inset 0 1px 1px rgba(255, 255, 255, 0.7);
            }}
            .month-header-row {{
                display: flex; justify-content: space-between; align-items: baseline;
                margin-bottom: 12px; padding: 0 4px;
            }}
            .month-title {{ font-size: 17px; font-weight: 700; color: var(--text-main); }}
            .month-subtotal {{ font-size: 13px; font-weight: 600; color: var(--apple-blue); }}

            .calendar-grid {{ 
                display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; 
            }}
            .cal-header {{ 
                text-align: center; font-size: 10px; font-weight: 700; color: var(--text-muted); padding-bottom: 6px; 
            }}
            .cal-cell {{ 
                aspect-ratio: 1; display: flex; justify-content: center; align-items: center; 
                font-size: 13.5px; font-weight: 500; color: var(--text-main); border-radius: 50%; 
                transition: transform 0.15s ease, background 0.15s ease;
            }}
            .cal-cell.has-work {{ 
                background: rgba(0, 113, 227, 0.16); 
                border: 1.5px solid rgba(0, 113, 227, 0.5); 
                color: var(--apple-blue); font-weight: 700; cursor: pointer; 
                box-shadow: 0 2px 6px rgba(0, 113, 227, 0.12);
            }}
            .cal-cell.has-work:active {{ transform: scale(0.88); background: rgba(0, 113, 227, 0.3); }}
            .cal-cell.empty {{ opacity: 0; pointer-events: none; }}

            /* WOCHEN-ANSICHT */
            .week-list, .entries-list {{ flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch; padding-bottom: 30px; }}
            .week-row {{ 
                background: var(--glass-card-bg); padding: 12px 14px; border-radius: 18px; 
                border: 1px solid var(--glass-border-light); display: flex; flex-direction: column; gap: 6px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.03), inset 0 1px 1px rgba(255,255,255,0.6); 
                cursor: pointer; transition: transform 0.15s ease; margin-bottom: 10px; 
            }}
            .week-row:active {{ transform: scale(0.97); }}
            .week-row-meta {{ display: flex; justify-content: space-between; font-size: 12.5px; font-weight: 600; color: var(--text-main); }}
            .timeline-track {{ height: 16px; background: rgba(0, 0, 0, 0.05); border-radius: 6px; position: relative; overflow: hidden; }}
            .timeline-bar {{ position: absolute; height: 100%; background: linear-gradient(90deg, #0071e3 0%, #4facfe 100%); border-radius: 4px; }}

            /* TAGES-ANSICHT */
            .day-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-shrink: 0; }}
            .nav-btn {{ 
                background: rgba(255, 255, 255, 0.5); border: 1px solid var(--glass-border-light); 
                border-radius: 50%; width: 36px; height: 36px; font-size: 13px; cursor: pointer; 
                display: flex; justify-content: center; align-items: center; flex-shrink: 0; 
                box-shadow: 0 2px 6px rgba(0,0,0,0.04); transition: transform 0.1s ease;
            }}
            .nav-btn:active {{ transform: scale(0.9); }}
            .nav-btn:disabled {{ opacity: 0.25; cursor: default; }}
            .day-date-title {{ font-size: 15px; font-weight: 700; color: var(--text-main); }}
            
            #day-content-animator {{ flex: 1; display: flex; flex-direction: column; overflow: hidden; }}

            .category-bars {{ margin-bottom: 15px; flex-shrink: 0; }}
            .cat-row {{ display: flex; align-items: center; margin-bottom: 8px; }}
            .cat-label {{ width: 85px; font-size: 12px; font-weight: 600; color: var(--text-muted); }}
            .bar-bg {{ flex: 1; height: 9px; background: rgba(0, 0, 0, 0.06); border-radius: 5px; overflow: hidden; margin: 0 10px; }}
            .bar-fill {{ height: 100%; background: linear-gradient(90deg, #0071e3 0%, #6366f1 100%); border-radius: 5px; }}
            .cat-time {{ width: 50px; text-align: right; font-size: 11.5px; font-weight: 700; color: var(--text-main); }}
            
            .entry-card {{ 
                background: var(--glass-card-bg); border-radius: 16px; padding: 13px 15px; 
                margin-bottom: 10px; border: 1px solid var(--glass-border-light); 
                box-shadow: 0 4px 14px rgba(0,0,0,0.03), inset 0 1px 1px rgba(255,255,255,0.7); 
            }}
            .entry-card-header {{ display: flex; justify-content: space-between; font-size: 12px; font-weight: 700; margin-bottom: 6px; color: var(--apple-blue); }}
            .entry-card-desc {{ font-size: 12.5px; color: var(--text-main); line-height: 1.5; }}
            
            .log-img {{ 
                max-width: 100%; height: auto; border-radius: 10px; margin-top: 10px; 
                border: 1px solid rgba(255,255,255,0.8); box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
                display: block; cursor: zoom-in; 
            }}

            /* LIGHTBOX */
            .lightbox {{ 
                display: none; position: fixed; z-index: 9999; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0, 0, 0, 0.55); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); 
                justify-content: center; align-items: center; opacity: 0; transition: opacity 0.25s ease; 
            }}
            .lightbox.active {{ opacity: 1; }}
            .lightbox img {{ max-width: 92vw; max-height: 85vh; border-radius: 16px; box-shadow: 0 25px 50px rgba(0,0,0,0.4); }}
        </style>
    </head>
    <body>

    <!-- Ambient Glowing Background Spheres -->
    <div class="ambient-background">
        <div class="glow-orb orb-1"></div>
        <div class="glow-orb orb-2"></div>
        <div class="glow-orb orb-3"></div>
    </div>

    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <img id="lightbox-img" src="" alt="Vollbild">
    </div>

    <div class="glass-panel" id="main-panel">
        <div class="global-stats">
            <div class="global-hours" id="render-global-total">0h 0m</div>
            <div class="global-label" id="stats-label">Arbeitszeit</div>
        </div>

        <div class="segmented-control" id="seg-control">
            <div class="slider-pill" id="pill"></div>
            <button class="control-btn">Monat</button>
            <button class="control-btn">Woche</button>
            <button class="control-btn">Tag</button>
        </div>

        <div class="view-container">
            <!-- MONATS-ANSICHT: Scroll-Container für alle Monate -->
            <div class="main-view active-view" id="view-month">
                <div class="month-scroll-container" id="month-carousel"></div>
            </div>

            <!-- WOCHEN-ANSICHT -->
            <div class="main-view" id="view-week">
                <div class="week-list" id="week-rows-wrapper"></div>
            </div>

            <!-- TAGES-ANSICHT -->
            <div class="main-view" id="view-day">
                <div class="day-header">
                    <button class="nav-btn" id="btn-prev" onclick="changeDay(-1)">&#10094;</button>
                    <div class="day-date-title" id="day-title">Datum</div>
                    <button class="nav-btn" id="btn-next" onclick="changeDay(1)">&#10095;</button>
                </div>
                
                <div id="day-content-animator">
                    <div id="day-categories-wrapper"></div>
                    <div class="entries-list" id="day-entries-wrapper"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const logData = {json_data};
        const dates = {json_dates};
        let currentDayIndex = dates.length > 0 ? dates.length - 1 : 0; 
        
        const views = ['month', 'week', 'day'];
        let currentActiveView = 'month'; 
        let currentIndex = 0;

        const segControl = document.getElementById('seg-control');
        const pill = document.getElementById('pill');
        const monthCarousel = document.getElementById('month-carousel');
        
        let activeMonthCard = null;

        const monthNames = [
            'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
            'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
        ];

        // --- HILFSFUNKTIONEN ---
        function formatHours(minutes) {{
            const h = Math.floor(minutes / 60);
            const m = Math.round(minutes % 60);
            return h + "h " + m + "m";
        }}

        function formatDayDate(dateString) {{
            const parts = dateString.split('-');
            const d = new Date(parts[0], parts[1] - 1, parts[2]);
            const days = ['So.', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.'];
            return days[d.getDay()] + " " + parseInt(parts[2], 10) + ". " + monthNames[d.getMonth()];
        }}

        // --- MONATSKALENDER DYNAMISCH GENERIEREN ---
        function getMonthRange() {{
            if (dates.length === 0) return [];
            const first = dates[0].split('-');
            const last = dates[dates.length - 1].split('-');
            
            let curYear = parseInt(first[0], 10);
            let curMonth = parseInt(first[1], 10);
            const endYear = parseInt(last[0], 10);
            const endMonth = parseInt(last[1], 10);
            
            const list = [];
            while (curYear < endYear || (curYear === endYear && curMonth <= endMonth)) {{
                list.push({{
                    year: curYear,
                    month: curMonth,
                    key: `${{curYear}}-${{String(curMonth).padStart(2, '0')}}`
                }});
                curMonth++;
                if (curMonth > 12) {{
                    curMonth = 1;
                    curYear++;
                }}
            }}
            return list;
        }}

        function initMonthCalendar() {{
            monthCarousel.innerHTML = '';
            const months = getMonthRange();
            
            months.forEach(m => {{
                let monthTotal = 0;
                for (const d in logData) {{
                    if (d.startsWith(m.key)) monthTotal += logData[d].total_minutes;
                }}

                const card = document.createElement('div');
                card.className = 'month-card';
                card.dataset.monthKey = m.key;
                card.dataset.monthName = `${{monthNames[m.month - 1]}} ${{m.year}}`;
                card.dataset.totalMins = monthTotal;

                const daysInMonth = new Date(m.year, m.month, 0).getDate();
                // 1. Wochentag im Monat (Montag = 0, ..., Sonntag = 6)
                const firstDayWeekday = (new Date(m.year, m.month - 1, 1).getDay() + 6) % 7;

                let gridHtml = `
                    <div class="month-header-row">
                        <div class="month-title">${{monthNames[m.month - 1]}} ${{m.year}}</div>
                        <div class="month-subtotal">${{formatHours(monthTotal)}}</div>
                    </div>
                    <div class="calendar-grid">
                        <div class="cal-header">MO</div><div class="cal-header">DI</div><div class="cal-header">MI</div>
                        <div class="cal-header">DO</div><div class="cal-header">FR</div><div class="cal-header">SA</div><div class="cal-header">SO</div>
                `;

                // Leerzellen vor dem 1. Tag
                for (let i = 0; i < firstDayWeekday; i++) {{
                    gridHtml += '<div class="cal-cell empty"></div>';
                }}

                // Tage 1 bis N
                for (let d = 1; d <= daysInMonth; d++) {{
                    const dateStr = `${{m.key}}-${{String(d).padStart(2, '0')}}`;
                    if (dateStr in logData) {{
                        gridHtml += `<div class="cal-cell has-work" onclick="forceDayView('${{dateStr}}')">${{d}}</div>`;
                    }} else {{
                        gridHtml += `<div class="cal-cell">${{d}}</div>`;
                    }}
                }}
                gridHtml += '</div>';
                card.innerHTML = gridHtml;
                monthCarousel.appendChild(card);
            }});

            // Standardmäßig zum letzten Monat scrollen (z. B. neuester Monat)
            const cards = monthCarousel.querySelectorAll('.month-card');
            if (cards.length > 0) {{
                const targetCard = cards[cards.length - 1];
                activeMonthCard = targetCard;
                setTimeout(() => {{
                    targetCard.scrollIntoView({{ behavior: 'auto', block: 'center' }});
                    updateMonthHeader(targetCard);
                }}, 60);
            }}
        }}

        // --- HEADER JE NACH ZENTRIERTEM MONAT AKTUALISIEREN ---
        function updateMonthHeader(card) {{
            if (!card) return;
            const totalMins = parseInt(card.dataset.totalMins || '0', 10);
            document.getElementById('render-global-total').innerText = formatHours(totalMins);
            document.getElementById('stats-label').innerText = `Arbeitszeit im ${{card.dataset.monthName}}`;
        }}

        // Erkennt in Echtzeit beim Scrollen den Monat in der Mitte des Bildschirms
        monthCarousel.addEventListener('scroll', () => {{
            if (currentActiveView !== 'month') return;
            
            const cards = monthCarousel.querySelectorAll('.month-card');
            const containerRect = monthCarousel.getBoundingClientRect();
            const containerCenter = containerRect.top + containerRect.height / 2;

            let closestCard = null;
            let minDistance = Infinity;

            cards.forEach(card => {{
                const cardRect = card.getBoundingClientRect();
                const cardCenter = cardRect.top + cardRect.height / 2;
                const dist = Math.abs(containerCenter - cardCenter);

                if (dist < minDistance) {{
                    minDistance = dist;
                    closestCard = card;
                }}
            }});

            if (closestCard && closestCard !== activeMonthCard) {{
                activeMonthCard = closestCard;
                updateMonthHeader(closestCard);
            }}
        }}, {{ passive: true }});

        // --- GESTEN & SEGMENTED CONTROL ---
        let isDragging = false;
        let startTouchX = 0;
        let initialPercent = 0;

        segControl.addEventListener('touchstart', (e) => {{
            isDragging = true;
            startTouchX = e.touches[0].clientX;
            initialPercent = currentIndex * 100;
            pill.style.transition = 'none';
        }}, {{ passive: false }});

        segControl.addEventListener('touchmove', (e) => {{
            if (!isDragging) return;
            e.preventDefault(); 
            const deltaX = e.touches[0].clientX - startTouchX;
            const deltaPercent = (deltaX / pill.offsetWidth) * 100;
            let newPercent = initialPercent + deltaPercent;
            if (newPercent < 0) newPercent = 0;
            if (newPercent > 200) newPercent = 200;
            pill.style.transform = `translateX(${{newPercent}}%)`;
        }}, {{ passive: false }});

        segControl.addEventListener('touchend', (e) => {{
            if (!isDragging) return;
            isDragging = false;
            pill.style.transition = 'transform 0.3s cubic-bezier(0.25, 1, 0.5, 1)';
            const deltaX = e.changedTouches[0].clientX - startTouchX;
            if (Math.abs(deltaX) < 5) {{
                pill.style.transform = `translateX(${{currentIndex * 100}}%)`;
                return;
            }}
            const deltaPercent = (deltaX / pill.offsetWidth) * 100;
            let newIndex = Math.round((initialPercent + deltaPercent) / 100);
            if (newIndex < 0) newIndex = 0;
            if (newIndex > 2) newIndex = 2;
            uiSwitchView(views[newIndex], newIndex);
        }});

        segControl.addEventListener('click', (e) => {{
            const rect = segControl.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const tabWidth = rect.width / 3;
            let newIndex = Math.floor(clickX / tabWidth);
            if (newIndex >= 0 && newIndex <= 2) {{
                uiSwitchView(views[newIndex], newIndex);
            }}
        }});

        // --- TAGESANSICHT WISCHGESTE ---
        const dayAnimator = document.getElementById('day-content-animator');
        let swipeStartX = 0;
        let swipeStartY = 0;

        dayAnimator.addEventListener('touchstart', (e) => {{
            swipeStartX = e.touches[0].clientX;
            swipeStartY = e.touches[0].clientY;
        }}, {{ passive: true }});

        dayAnimator.addEventListener('touchend', (e) => {{
            const deltaX = e.changedTouches[0].clientX - swipeStartX;
            const deltaY = e.changedTouches[0].clientY - swipeStartY;
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 40) {{
                if (deltaX < 0 && currentDayIndex < dates.length - 1) {{
                    changeDay(1);
                }} else if (deltaX > 0 && currentDayIndex > 0) {{
                    changeDay(-1);
                }}
            }}
        }}, {{ passive: true }});

        // --- ANSICHTEN WECHSELN ---
        function uiSwitchView(viewId, index) {{
            currentActiveView = viewId;
            currentIndex = index;
            pill.style.transform = `translateX(${{index * 100}}%)`;
            
            document.querySelectorAll('.main-view').forEach(v => v.classList.remove('active-view'));
            document.getElementById(`view-${{viewId}}`).classList.add('active-view');
            updateDynamicCounter(viewId);
        }}

        function updateDynamicCounter(viewId) {{
            const totalDisplay = document.getElementById('render-global-total');
            const label = document.getElementById('stats-label');
            
            if (viewId === 'month') {{
                if (activeMonthCard) {{
                    updateMonthHeader(activeMonthCard);
                }}
            }} 
            else if (viewId === 'week') {{
                let sum = 0;
                for (let date in logData) sum += logData[date].total_minutes;
                totalDisplay.innerText = formatHours(sum);
                label.innerText = "Gesamte protokollierte Arbeitszeit";
            }} 
            else if (viewId === 'day') {{
                const dStr = dates[currentDayIndex];
                if (dStr && logData[dStr]) {{
                    totalDisplay.innerText = formatHours(logData[dStr].total_minutes);
                    label.innerText = "Arbeitszeit am " + formatDayDate(dStr);
                }}
            }}
        }}

        function forceDayView(dateStr) {{
            currentDayIndex = dates.indexOf(dateStr);
            renderDayView();
            uiSwitchView('day', 2);
        }}

        function openLightbox(src) {{
            const lb = document.getElementById('lightbox');
            document.getElementById('lightbox-img').src = src;
            lb.style.display = 'flex';
            setTimeout(() => lb.classList.add('active'), 10);
        }}

        function closeLightbox() {{
            const lb = document.getElementById('lightbox');
            lb.classList.remove('active');
            setTimeout(() => lb.style.display = 'none', 250);
        }}

        function initWeekTimeline() {{
            const wrapper = document.getElementById('week-rows-wrapper');
            wrapper.innerHTML = '';
            for (let i = 0; i < dates.length; i++) {{
                const dateStr = dates[i];
                const dayObj = logData[dateStr];
                const row = document.createElement('div');
                row.className = 'week-row';
                row.onclick = function() {{ forceDayView(dateStr); }};
                
                let bars = '';
                for (let j = 0; j < dayObj.entries.length; j++) {{
                    const e = dayObj.entries[j];
                    bars += `<div class="timeline-bar" style="left: ${{(e.start_min/1440)*100}}%; width: ${{(e.duration/1440)*100}}%;"></div>`;
                }}
                row.innerHTML = `<div class="week-row-meta"><span>${{formatDayDate(dateStr)}}</span><span>${{formatHours(dayObj.total_minutes)}}</span></div><div class="timeline-track">${{bars}}</div>`;
                wrapper.appendChild(row);
            }}
        }}

        function renderDayView() {{
            if (dates.length === 0) return;
            const data = logData[dates[currentDayIndex]];
            document.getElementById('day-title').innerText = formatDayDate(dates[currentDayIndex]);
            
            let maxCatTime = 0;
            for (let cat in data.categories) if (data.categories[cat] > maxCatTime) maxCatTime = data.categories[cat];
            
            let catHtml = '<div class="category-bars">';
            for (let cat in data.categories) {{
                catHtml += `<div class="cat-row"><div class="cat-label">${{cat}}</div><div class="bar-bg"><div class="bar-fill" style="width: ${{(data.categories[cat] / maxCatTime) * 100}}%;"></div></div><div class="cat-time">${{formatHours(data.categories[cat])}}</div></div>`;
            }}
            document.getElementById('day-categories-wrapper').innerHTML = catHtml + '</div>';

            let entriesHtml = '';
            for (let i = 0; i < data.entries.length; i++) {{
                let e = data.entries[i];
                entriesHtml += `<div class="entry-card"><div class="entry-card-header"><span>${{e.category}}</span><span>${{e.start}} - ${{e.end}}</span></div><div class="entry-card-desc">${{e.desc}}</div></div>`;
            }}
            document.getElementById('day-entries-wrapper').innerHTML = entriesHtml;
            
            document.querySelectorAll('.log-img').forEach(img => {{
                img.onclick = function() {{ openLightbox(this.src); }};
            }});

            document.getElementById('btn-prev').disabled = currentDayIndex === 0;
            document.getElementById('btn-next').disabled = currentDayIndex === dates.length - 1;
        }}

        function changeDay(dir) {{
            let nextIdx = currentDayIndex + dir;
            if (nextIdx >= 0 && nextIdx < dates.length) {{ 
                currentDayIndex = nextIdx;
                const animator = document.getElementById('day-content-animator');
                
                animator.style.transition = 'none';
                animator.style.opacity = '0';
                animator.style.transform = dir > 0 ? 'translateX(30px)' : 'translateX(-30px)';
                
                setTimeout(() => {{
                    renderDayView();
                    updateDynamicCounter('day');
                    animator.style.transition = 'transform 0.3s cubic-bezier(0.25, 1, 0.5, 1), opacity 0.3s ease';
                    animator.style.transform = 'translateX(0)';
                    animator.style.opacity = '1';
                }}, 20);
            }}
        }}

        // Start initialisieren
        initMonthCalendar();
        initWeekTimeline();
        renderDayView();
    </script>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"{output_file} erfolgreich geupdatet!")

if __name__ == "__main__":
    markdown_file = "arbeitszeit_log.md"
    parsed_data, total_mins = parse_markdown_log(markdown_file)
    if parsed_data:
        generate_html_dashboard(parsed_data, total_mins)