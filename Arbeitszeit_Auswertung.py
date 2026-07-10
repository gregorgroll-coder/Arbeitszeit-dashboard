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
            
            # Markdown Bilder umwandeln und klickbar machen
            desc_html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" class="log-img" title="Zum Vergrößern klicken">', desc)
            
            # Fetten Text (**Text**) in edle Überschriften umwandeln
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
    
    month_sum = sum(day["total_minutes"] for date, day in data.items() if date.startswith("2026-07"))
    initial_hours_str = f"{int(month_sum // 60)}h {int(month_sum % 60)}m"
    initial_label = "Arbeitszeit im Juli 2026"

    cal_html_ssr = ""
    padding_cells = 2
    for _ in range(padding_cells): cal_html_ssr += '<div class="cal-cell empty"></div>'
    for d in range(1, 32):
        match_str = f"2026-07-{d:02d}"
        if match_str in data: cal_html_ssr += f'<div class="cal-cell has-work" onclick="forceDayView(\'{match_str}\')">{d}</div>'
        else: cal_html_ssr += f'<div class="cal-cell">{d}</div>'

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
        
        <meta name="theme-color" content="#5b9ff9">
        
        <title>Arbeitszeit Cockpit</title>
        <style>
            :root {{ 
                --text-main: #1d1d1f; 
                --text-muted: #6e6e73; 
                --glass-bg: rgba(255, 255, 255, 0.25);
                --glass-border: rgba(255, 255, 255, 0.35);
            }}
            
            * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
            
            /* --- iOS SAFE AREA & BODY LOCK FIX --- */
            html {{
                height: -webkit-fill-available;
            }}
            
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; 
                background: linear-gradient(135deg, #5b9ff9 0%, #7ee8fa 100%); 
                min-height: 100vh;
                min-height: -webkit-fill-available;
                margin: 0; padding: 0; 
                overflow: hidden; /* Verhindert das Wackeln des gesamten Bildschirms */
                position: fixed; /* Sperrt den Hintergrund extrem fest, Apple kann hier keine Ränder mehr zeichnen */
                top: 0; left: 0; width: 100%;
                display: flex; justify-content: center; align-items: center; 
            }}
            
            .glass-panel {{
                width: 100%; height: 100%; 
                background: var(--glass-bg); 
                backdrop-filter: blur(35px); -webkit-backdrop-filter: blur(35px);
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
                border: 1px solid var(--glass-border);
                display: flex; flex-direction: column; position: relative; overflow: hidden; 
                /* Dynamisches Padding um oben die Notch und unten den Home-Balken weich zu umgehen */
                padding: max(env(safe-area-inset-top), 40px) 25px max(env(safe-area-inset-bottom), 20px) 25px; 
            }}
            
            @media (min-width: 550px) {{
                .glass-panel {{
                    height: 90vh; max-width: 480px; max-height: 880px;
                    border-radius: 44px;
                    padding-top: 30px; padding-bottom: 25px;
                }}
            }}
            
            .global-stats {{ text-align: center; margin-bottom: 15px; margin-top: 10px; flex-shrink: 0; }}
            .global-hours {{ font-size: 46px; font-weight: 700; letter-spacing: -1.5px; color: var(--text-main); line-height: 1; }}
            .global-label {{ font-size: 12px; color: var(--text-muted); font-weight: 600; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.8px; }}

            .segmented-control {{ position: relative; display: flex; background: rgba(0, 0, 0, 0.05); border-radius: 14px; padding: 3px; margin-bottom: 20px; border: 0.5px solid rgba(255, 255, 255, 0.3); flex-shrink: 0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }}
            .control-btn {{ flex: 1; border: none; background: none; padding: 8px 0; font-size: 13px; font-weight: 600; color: var(--text-main); cursor: pointer; z-index: 2; }}
            
            /* Der Slider reagiert jetzt nicht mehr auf CSS-Transitions beim Wischen, da JS in Echtzeit trackt */
            .slider-pill {{ position: absolute; top: 3px; left: 3px; width: calc(33.333% - 4px); height: calc(100% - 6px); background: rgba(255, 255, 255, 0.95); box-shadow: 0 3px 8px rgba(0,0,0,0.08); border-radius: 11px; z-index: 1; }}
            .slider-pill.smooth-snap {{ transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1); }}

            /* --- STUFENLOSES SWIPE & SCROLL DESIGN --- */
            .view-container {{ 
                flex: 1; position: relative; width: 100%; 
                display: flex; overflow-x: auto; overflow-y: hidden; 
                scroll-snap-type: x mandatory; /* Zieht die Ansicht magnetisch auf die aktuelle Seite */
                scroll-behavior: auto; /* Wird bei Buttons über JS gesteuert */
                scrollbar-width: none; -webkit-overflow-scrolling: touch; 
            }}
            .view-container::-webkit-scrollbar {{ display: none; }}
            
            .main-view {{ 
                min-width: 100%; height: 100%; 
                scroll-snap-align: center; /* Magnet-Punkt */
                display: flex; flex-direction: column; overflow: hidden;
            }}

            .calendar-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; background: rgba(255, 255, 255, 0.3); padding: 15px; border-radius: 22px; border: 1px solid rgba(255, 255, 255, 0.4); box-shadow: 0 10px 20px rgba(0,0,0,0.02); }}
            .cal-header {{ text-align: center; font-size: 10px; font-weight: 700; color: var(--text-muted); padding-bottom: 5px; }}
            .cal-cell {{ aspect-ratio: 1; display: flex; justify-content: center; align-items: center; font-size: 14px; font-weight: 500; color: var(--text-main); border-radius: 50%; }}
            .cal-cell.has-work {{ background: rgba(37, 117, 252, 0.15); border: 1.5px solid rgba(37, 117, 252, 0.4); color: #004999; font-weight: 700; cursor: pointer; }}
            .cal-cell.empty {{ opacity: 0.15; }}
            .calendar-title {{ font-size: 18px; font-weight: 700; margin-bottom: 12px; padding-left: 5px; color: var(--text-main); }}

            .week-list {{ display: flex; flex-direction: column; gap: 12px; overflow-y: auto; padding-right: 4px; padding-bottom: 40px; overscroll-behavior-y: contain; }}
            .week-row {{ background: rgba(255, 255, 255, 0.3); padding: 12px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.4); display: flex; flex-direction: column; gap: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.02); cursor: pointer; transition: transform 0.15s ease, background 0.15s ease; }}
            .week-row:active {{ transform: scale(0.97); background: rgba(255, 255, 255, 0.5); }}
            .week-row-meta {{ display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; color: var(--text-main); }}
            .timeline-track {{ height: 18px; background: rgba(0, 0, 0, 0.04); border-radius: 6px; position: relative; overflow: hidden; }}
            .timeline-bar {{ position: absolute; height: 100%; background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); border-radius: 4px; }}
            .timeline-labels {{ display: flex; justify-content: space-between; font-size: 9px; color: var(--text-muted); padding: 0 2px; }}

            .day-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-shrink: 0; }}
            .nav-btn {{ background: rgba(255, 255, 255, 0.45); border: 1px solid rgba(255,255,255,0.5); border-radius: 50%; width: 36px; height: 36px; font-size: 13px; cursor: pointer; display: flex; justify-content: center; align-items: center; flex-shrink: 0; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }}
            .nav-btn:disabled {{ opacity: 0.2; cursor: default; }}
            .day-date-title {{ font-size: 15px; font-weight: 600; }}
            
            .category-bars {{ margin-bottom: 15px; flex-shrink: 0; }}
            .cat-row {{ display: flex; align-items: center; margin-bottom: 8px; }}
            .cat-label {{ width: 80px; font-size: 12px; font-weight: 600; }}
            .bar-bg {{ flex: 1; height: 10px; background: rgba(255, 255, 255, 0.4); border-radius: 5px; overflow: hidden; margin: 0 10px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05); }}
            .bar-fill {{ height: 100%; background: linear-gradient(90deg, #2575fc 0%, #6a11cb 100%); border-radius: 5px; }}
            .cat-time {{ width: 50px; text-align: right; font-size: 11px; font-weight: 600; }}
            
            .entries-list {{ flex: 1; overflow-y: auto; padding-bottom: 40px; overscroll-behavior-y: contain; }}
            .entry-card {{ background: rgba(255, 255, 255, 0.45); border-radius: 14px; padding: 12px 15px; margin-bottom: 10px; border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 4px 15px rgba(0,0,0,0.02); }}
            .entry-card-header {{ display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; margin-bottom: 8px; }}
            .entry-card-desc {{ font-size: 12px; color: #2c2c2e; line-height: 1.5; }}
            
            .log-img {{ max-width: 100%; height: auto; border-radius: 10px; margin-top: 10px; margin-bottom: 4px; border: 1px solid rgba(255,255,255,0.7); box-shadow: 0 4px 12px rgba(0,0,0,0.08); display: block; cursor: zoom-in; transition: transform 0.2s; }}
            .log-img:active {{ transform: scale(0.98); }}

            .lightbox {{ display: none; position: fixed; z-index: 9999; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); justify-content: center; align-items: center; opacity: 0; transition: opacity 0.25s ease; }}
            .lightbox.active {{ opacity: 1; }}
            .lightbox img {{ max-width: 95vw; max-height: 85vh; border-radius: 16px; box-shadow: 0 25px 50px rgba(0,0,0,0.5); transform: scale(0.95); transition: transform 0.25s cubic-bezier(0.25, 1, 0.5, 1); }}
            .lightbox.active img {{ transform: scale(1); }}
        </style>
    </head>
    <body>

    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <img id="lightbox-img" src="" alt="Vollbild">
    </div>

    <div class="glass-panel" id="main-panel">
        <div class="global-stats">
            <div class="global-hours" id="render-global-total">{initial_hours_str}</div>
            <div class="global-label" id="stats-label">{initial_label}</div>
        </div>

        <div class="segmented-control">
            <div class="slider-pill smooth-snap" id="pill"></div>
            <button class="control-btn" onclick="uiSwitchView('month', 0)">Monat</button>
            <button class="control-btn" onclick="uiSwitchView('week', 1)">Woche</button>
            <button class="control-btn" onclick="uiSwitchView('day', 2)">Tag</button>
        </div>

        <div class="view-container" id="view-container">
            <div class="main-view" id="view-month">
                <div class="calendar-title">Juli 2026</div>
                <div class="calendar-grid" id="calendar-wrapper">
                    <div class="cal-header">MO</div><div class="cal-header">DI</div><div class="cal-header">MI</div>
                    <div class="cal-header">DO</div><div class="cal-header">FR</div><div class="cal-header">SA</div><div class="cal-header">SO</div>
                    {cal_html_ssr}
                </div>
            </div>

            <div class="main-view" id="view-week">
                <div class="week-list" id="week-rows-wrapper"></div>
            </div>

            <div class="main-view" id="view-day">
                <div class="day-header">
                    <button class="nav-btn" id="btn-prev" onclick="changeDay(-1)">&#10094;</button>
                    <div class="day-date-title" id="day-title">Datum</div>
                    <button class="nav-btn" id="btn-next" onclick="changeDay(1)">&#10095;</button>
                </div>
                <div id="day-categories-wrapper"></div>
                <div class="entries-list" id="day-entries-wrapper"></div>
            </div>
        </div>
    </div>

    <script>
        const logData = {json_data};
        const dates = {json_dates};
        let currentDayIndex = dates.length - 1; 
        
        const views = ['month', 'week', 'day'];
        let currentActiveView = 'month'; 
        
        const viewContainer = document.getElementById('view-container');
        const pill = document.getElementById('pill');

        // --- STUFENLOSER SCHIEBER (Scroll Sync) ---
        // Wenn man wischt, wird die Position des Schiebers in Echtzeit relativ zur Fingerbewegung berechnet
        viewContainer.addEventListener('scroll', () => {{
            const width = viewContainer.clientWidth;
            if(width === 0) return;
            
            // fraction ist 0.0 (Monat), 1.0 (Woche) oder 2.0 (Tag)
            const fraction = viewContainer.scrollLeft / width;
            
            // Schieber wandert exakt mit
            pill.style.transform = `translateX(${{fraction * 100}}%)`;
            
            // Ermittle, welche Ansicht gerade dominant ist
            const activeIndex = Math.round(fraction);
            if (currentActiveView !== views[activeIndex]) {{
                currentActiveView = views[activeIndex];
                updateDynamicCounter(currentActiveView);
            }}
        }}, {{ passive: true }});

        // --- BUTTON KLICKS ---
        function uiSwitchView(viewId, index) {{
            // Aktiviert das butterweiche CSS-Snapping beim Button-Klick
            viewContainer.scrollTo({{
                left: index * viewContainer.clientWidth,
                behavior: 'smooth'
            }});
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

        function formatHours(minutes) {{
            const h = Math.floor(minutes / 60);
            const m = Math.round(minutes % 60);
            return h + "h " + m + "m";
        }}

        function formatDayDate(dateString) {{
            const parts = dateString.split('-');
            const d = new Date(parts[0], parts[1] - 1, parts[2]);
            const days = ['So.', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.'];
            const months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
            return days[d.getDay()] + " " + parts[2] + ". " + months[d.getMonth()];
        }}

        function updateDynamicCounter(viewId) {{
            const totalDisplay = document.getElementById('render-global-total');
            const label = document.getElementById('stats-label');
            if (viewId === 'month') {{
                let sum = 0;
                for (let date in logData) if (date.indexOf('2026-07') === 0) sum += logData[date].total_minutes;
                totalDisplay.innerText = formatHours(sum);
                label.innerText = "Arbeitszeit im Juli 2026";
            }} 
            else if (viewId === 'week') {{
                let sum = 0;
                for (let date in logData) sum += logData[date].total_minutes;
                totalDisplay.innerText = formatHours(sum);
                label.innerText = "Gesamte Arbeitszeit der Woche";
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

        function initWeekTimeline() {{
            const wrapper = document.getElementById('week-rows-wrapper');
            for(let i=0; i<dates.length; i++) {{
                const dateStr = dates[i];
                const dayObj = logData[dateStr];
                const row = document.createElement('div');
                row.className = 'week-row';
                
                row.onclick = function() {{ forceDayView(dateStr); }};
                
                let bars = '';
                for(let j=0; j<dayObj.entries.length; j++) {{
                    const e = dayObj.entries[j];
                    bars += '<div class="timeline-bar" style="left: ' + ((e.start_min/1440)*100) + '%; width: ' + ((e.duration/1440)*100) + '%;"></div>';
                }}
                row.innerHTML = `<div class="week-row-meta"><span>${{formatDayDate(dateStr)}}</span><span>${{formatHours(dayObj.total_minutes)}}</span></div><div class="timeline-track">${{bars}}</div>`;
                wrapper.appendChild(row);
            }}
        }}

        function renderDayView() {{
            if(dates.length === 0) return;
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
            for(let i=0; i<data.entries.length; i++) {{
                let e = data.entries[i];
                entriesHtml += `<div class="entry-card"><div class="entry-card-header"><span>${{e.category}}</span><span>${{e.start}} - ${{e.end}}</span></div><div class="entry-card-desc">${{e.desc}}</div></div>`;
            }}
            document.getElementById('day-entries-wrapper').innerHTML = entriesHtml;
            
            const images = document.querySelectorAll('.log-img');
            for(let i=0; i<images.length; i++) {{
                images[i].onclick = function() {{ openLightbox(this.src); }};
            }}

            document.getElementById('btn-prev').disabled = currentDayIndex === 0;
            document.getElementById('btn-next').disabled = currentDayIndex === dates.length - 1;
        }}

        function changeDay(dir) {{
            let nextIdx = currentDayIndex + dir;
            if(nextIdx >= 0 && nextIdx < dates.length) {{ currentDayIndex = nextIdx; renderDayView(); updateDynamicCounter('day'); }}
        }}

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