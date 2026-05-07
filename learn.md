# learn.md — Learnings (stealth-lora)

> **Zweck**: Positive Erkenntnisse und Best Practices.

---

## 2026-05-07

### Doc-System Bootstrap
- **Erkenntnis**: Standardisierte Pflichtdateien machen Repos agenten-lesbar
- **Best Practice**: Jedes Repo braucht sinrules.md + brain.md + registry.md als Minimum

## §Q — LIVE CRASH-TEST DISCOVERIES (2026-05-07) 🔥🔥🔥

> **Entdeckt während einem 90-Minuten Live-Debugging-Marathon mit heypiggy Dashboard + Qualtrics Survey.**
> **9 kritische Root Causes gefunden und gefixt. Survey-Klicks funktionieren jetzt!**

---

### §Q1 — SURVEYS OPEN IN NEW TABS (KRITISCH)

**Entdeckung:** Qualtrics/Samplicio Surveys öffnen in NEUEN Chrome Tabs mit anderen URLs (z.B. `bceconsulting.az1.qualtrics.com`). Unser CDP war 90% der Session mit dem FALSCHEN Tab verbunden.

```python
def click_survey(pid, survey_id):
    tabs_before = len(list_browser_tabs(port))
    
    # CDP JS: clickSurvey('ID') im Dashboard
    ws_dashboard.send(json.dumps({
        "id": 1, "method": "Runtime.evaluate",
        "params": {"expression": f"clickSurvey('{survey_id}')"}
    }))
    
    time.sleep(3)  # Tab öffnet sich
    
    tabs_after = list_browser_tabs(port)
    if len(tabs_after) > tabs_before:
        new_tab = tabs_after[-1]  # New tab is LAST
        print(f"[TAB] Survey opened in NEW tab: {new_tab['url'][:60]}")
        connect_to_tab(new_tab['id'])  # ← Connect to CORRECT tab!
    else:
        print("[TAB] No new tab — survey loaded in-page")
```

**Resultat:** Nach diesem Fix konnte CDP `Runtime.evaluate` tatsächlich Survey-Elemente finden. Vorher: 0 matches. Nachher: 20+ matches.

---

### §Q2 — MULTIPLE STACKED MODALS (7-9 LAYERS)

**Entdeckung:** Das heypiggy Dashboard hat 7-9 gelayerte Modals (Welcome Bonus Streak, Account Settings, Name Confirmation, Push Notification Prompt, Rating Prompt) — ALLE mit identischem `z-index` und überlappenden Koordinaten. Ein Klick auf "Nächste" bei (600,547) trifft stattdessen ein "Schließen"-Button im darunter liegenden Modal.

```javascript
// DIESE Modals sind ALLE gleichzeitig im DOM:
// 1. Welcome-Bonus-Streak Modal (z-index: 1000)
// 2. Account-Settings Modal (z-index: 1000)
// 3. Name-Confirmation Modal (z-index: 1000)
// 4. Push-Notification Modal (z-index: 1000)
// 5. Rating-Prompt Modal (z-index: 1000)
// → Klick auf "Nächste" hit "Schließen" statt richtigen Button!

// FIX: Alle gestackten Modals per JS schließen VOR Survey-Interaktion:
(function closeAllModals() {
    const closeButtons = document.querySelectorAll(
        'button[aria-label="Close"], button.close, .modal-close, ' +
        '[class*="close"], [class*="Close"], .btn-close, .b-close, ' +
        'div[role="dialog"] button:first-child'
    );
    let closed = 0;
    closeButtons.forEach(btn => {
        try {
            btn.click();
            closed++;
        } catch(e) {}
    });
    // Auch per Text finden:
    document.querySelectorAll('button, span, div[role="button"]').forEach(el => {
        const t = (el.textContent || '').trim();
        if (t === 'Schließen' || t === 'Close' || t === '×' || t === '✕') {
            try { el.click(); closed++; } catch(e) {}
        }
    });
    console.log(`[MODAL] Closed ${closed} stacked modals`);
})();
```

---

### §Q3 — REACT FORM FILLING REQUIRES NATIVE SETTER

**Entdeckung:** React-Controlled Inputs ignorieren `el.value = "text"` komplett. Der React State wird NICHT aktualisiert. Muss den nativen Property-Setter nutzen + Events dispatchen.

```javascript
// FALSCH (React ignoriert):
el.value = "Berlin";  // ❌ DOM updated, aber React State bleibt leer!

// RICHTIG — Native Setter + Input + Change Events:
function reactFill(el, value) {
    // Step 1: Native value setter (überschreibt React's synthetic setter)
    const nativeSetter = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype, 'value'
    ).set;
    nativeSetter.call(el, value);
    
    // Step 2: React events in richtiger Reihenfolge
    el.dispatchEvent(new Event('input',  { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    
    // Step 3: Optional blur/focus für Material/Angular
    el.dispatchEvent(new FocusEvent('focus', { bubbles: true }));
    el.dispatchEvent(new FocusEvent('blur',  { bubbles: true }));
}

// Alternative für Text-Insertion (funktioniert bei contentEditable + inputs):
document.execCommand('insertText', false, value);

// Anwendung auf heypiggy Pre-Survey-Form:
reactFill(document.getElementById('Zip'), '10785');
reactFill(document.getElementById('Age'), '32');
```

**Resultat:** Vor diesem Fix blieben Zip/Age-Felder leer → Survey schlug fehl. Nach Fix: Felder korrekt befüllt, Formular validiert, Survey startet.

---

### §Q4 — QUALTRICS LANGUAGE SELECT IS `<select>` DROPDOWN

**Entdeckung:** Der Qualtrics Language Picker ist ein natives `<select class="Q_lang">` Element mit `<option>Deutsch</option>`, KEINE klickbaren Label-Buttons. Nach der Sprachauswahl sortiert Qualtrics die Länderoptionen um (Deutschland wandert an die Spitze).

```javascript
// FALSCH (Button-Klick-Ansatz):
const langBtn = document.querySelector('button:has-text("Deutsch")');
langBtn.click();  // ❌ Kein Button — es ist ein <select>!

// RICHTIG — Select-Element per selectedIndex setzen:
const langSelect = document.querySelector('select.Q_lang');
for (let i = 0; i < langSelect.options.length; i++) {
    if (langSelect.options[i].text.trim() === 'Deutsch') {
        langSelect.selectedIndex = i;
        langSelect.dispatchEvent(new Event('change', { bubbles: true }));
        break;
    }
}

// ACHTUNG: Nach change-Event reordert Qualtrics die Optionen!
// Vor Auswahl: [Deutsch (unten), ...]
// Nach Auswahl: [Deutschland (oben), ...]
// → IMMER warten bis DOM-Update abgeschlossen ist:
await new Promise(r => setTimeout(r, 1000));

// JETZT erst Länderauswahl treffen:
const countryRadios = document.querySelectorAll('input[type="radio"]');
// Deutschland ist jetzt an Position 0 statt vorher an Position X
```

---

### §Q5 — BALANCE READ BUG (125.00€ statt 2.23€)

**Entdeckung:** `scanner.read_balance()` nutzte `Math.max(...)` auf ALLEN €-Werten der Seite. Der Level-Fortschrittstext "125" erschien zufällig neben einem €-Symbol, wodurch die Balance fälschlich als 125.00€ gelesen wurde.

```python
# FALSCH (scanner.read_balance):
text = document.body.innerText
matches = re.findall(r'(\d+[.,]\d{2})\s*€', text)
values = [float(m.replace(',', '.')) for m in matches]
balance = max(values)  # ❌ 125.00 (Level) statt 2.23 (Balance)!

# RICHTIG — Kontext-Filterung:
def read_balance(ws):
    result = ws.send(json.dumps({
        "id": 1, "method": "Runtime.evaluate",
        "params": {"expression": """
            (function() {
                const text = document.body.innerText;
                const lines = text.split('\\n');
                let balance = 0.0;
                
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i];
                    const m = line.match(/(\\d+[.,]\\d{2})\\s*€/);
                    if (!m) continue;
                    
                    const val = parseFloat(m[1].replace(',', '.'));
                    
                    // FILTER: Nur plausible Balance-Werte (0.01 - 50.00€)
                    if (val < 0.01 || val > 50.0) continue;
                    
                    // FILTER: Keine Level/Min/Progress-Kontextwörter
                    const context = (lines[i-1] || '') + ' ' + line + ' ' + (lines[i+1] || '');
                    if (/Level|Min|Progress|Punkte|Streak|Bonus/i.test(context)) continue;
                    
                    // FILTER: Bevorzuge Werte NACH "Guthaben"/"Balance"/"Kontostand"
                    if (/Guthaben|Balance|Kontostand|€/.test(lines[i-1] || '') && val > balance) {
                        balance = val;
                    } else if (balance === 0.0) {
                        balance = val;  // Fallback: erster valider Wert
                    }
                }
                return { balance, method: 'filtered' };
            })()
        """}
    }))
    data = json.loads(result)['result']['result']['value']
    return float(data['balance'])
```

---

### §Q6 — FILL-BY-ELEMENT-ID IS MOST RELIABLE

**Entdeckung:** Angular Material/React generieren dynamische IDs wie `mat-input-2`, `Age`, `Zip`, `mat-radio-0-input`. `getElementById('Age')` ist VIEL zuverlässiger als `querySelector`-basierte Ansätze. Das heypiggy Pre-Survey-Form verwendet konsistent IDs.

```javascript
// FALSCH — querySelector mit unsicheren Selektoren:
document.querySelector('input[placeholder*="Alter"]')   // ❌ Kein placeholder
document.querySelector('.mat-input-element:nth-child(3)') // ❌ Index ändert sich
document.querySelector('input[type="text"]')               // ❌ Findet falsches Feld

// RICHTIG — getElementById (heypiggy Form IDs sind STABIL):
const formFields = {
    zip:    document.getElementById('Zip'),              // Textarea
    age:    document.getElementById('Age'),              // Input
    gender: document.getElementById('mat-radio-2-input'), // Männlich
    job:    document.getElementById('mat-radio-6-input'), // Angestellter
    next:   document.getElementById('next_0'),           // Submit button
};

// Fill form:
reactFill(formFields.zip, persona.plz);
reactFill(formFields.age, String(persona.age));
formFields.gender.click();
formFields.job.click();
formFields.next.click();
```

**Warum IDs stabil sind:**
- Angular: `mat-input-2` → index-basiert, aber IDs ändern sich nur bei Komponenten-Reihenfolge
- heypiggy: `Zip`, `Age`, `next_0` → hardcoded, ändern sich NIE
- React: dynamische IDs sind seltener, aber `id="Age"` bleibt stabil

---

### §Q7 — CDP Input.dispatchMouseEvent FOR REAL CLICKS

**Entdeckung:** `element.click()` via CDP `Runtime.evaluate` failt bei gelayerten React Modals. Der Klick "verschwindet" in der Event-Queue. CDP's `Input.dispatchMouseEvent` mit `type:'mousePressed'/'mouseReleased'` an exakten Koordinaten funktioniert ZUVERLÄSSIG — es simuliert echte User-Klicks durch ALLE Layer.

```python
def cdp_real_click(ws, x, y):
    """Echter Klick via CDP Input.dispatchMouseEvent — durchdringt ALLE Layer."""
    events = [
        {"type": "mouseMoved",   "x": x, "y": y, "button": "left", "clickCount": 0},
        {"type": "mousePressed",  "x": x, "y": y, "button": "left", "clickCount": 1},
        {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1},
    ]
    for i, evt in enumerate(events):
        ws.send(json.dumps({
            "id": 1000 + i,
            "method": "Input.dispatchMouseEvent",
            "params": evt
        }))
        time.sleep(0.05)  # Realistische Inter-Event-Delay
    
    # Verify: Response checken
    for i in range(len(events)):
        resp = json.loads(ws.recv())
        if "error" in resp:
            raise CDPClickError(f"CDP click failed: {resp['error']}")

# Verwendung:
bbox = element['bounds']  # {x, y, width, height}
center_x = bbox['x'] + bbox['width'] / 2
center_y = bbox['y'] + bbox['height'] / 2
cdp_real_click(ws, center_x, center_y)
```

**Warum `Runtime.evaluate(el.click())` failt:**
- React Synthetic Events: `el.click()` triggert kein `isTrusted=true` Event
- Modal-Layer: Das Event erreicht nicht das richtige DOM-Element
- Angular Zone.js: patched Event-Handler erkennen synthetische Events

**Warum `Input.dispatchMouseEvent` funktioniert:**
- OS-Level Event → `isTrusted: true`
- Koordinaten-basiert → kein DOM-Element-Targeting nötig
- Durchdringt ALLE z-index Layer (wie echter Mausklick)
- Funktioniert bei React, Angular, Vue, und nativem HTML

---

### §Q8 — CUA-DRIVER NEEDS `--force-renderer-accessibility`

**Entdeckung:** cua-driver returned 0 AX-Elemente wenn Chrome OHNE `--force-renderer-accessibility` Flag gestartet wurde. Chrome, das von opencode oder webauto-nodriver gestartet wird, hat dieses Flag NICHT → cua-driver ist blind.

```bash
# FALSCH (cua-driver sieht nichts):
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9999 \
  --remote-allow-origins=* \
  --user-data-dir=/tmp/bot-profile \
  'https://heypiggy.com'

$ cua-driver call get_window_state '{"pid":12345,"window_id":56789}'
→ {"children": []}  # ❌ 0 Elemente!

# RICHTIG (cua-driver sieht ALLES):
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9999 \
  --remote-allow-origins=* \
  --force-renderer-accessibility \
  --user-data-dir=/tmp/bot-profile \
  'https://heypiggy.com'

$ cua-driver call get_window_state '{"pid":12345,"window_id":56789}'
→ {"children": [254 elements]}  # ✅ Alle AX-Elemente sichtbar!
```

**Checklist vor Session-Start:**
```python
def verify_accessibility(pid, wid):
    """Verify cua-driver can see AX elements."""
    result = subprocess.run(
        ['cua-driver', 'call', 'get_window_state', json.dumps({"pid": pid, "window_id": wid})],
        capture_output=True, text=True, timeout=10
    )
    data = json.loads(result.stdout)
    child_count = len(data.get('children', []))
    
    if child_count == 0:
        raise AccessibilityError(
            "cua-driver sees 0 AX elements! "
            "Chrome needs --force-renderer-accessibility flag. "
            "Restart Chrome with the flag and try again."
        )
    
    print(f"[AX] cua-driver sees {child_count} elements ✅")
    return child_count
```

**Playstealth Fix:**
```bash
# playstealth setzt --force-renderer-accessibility NICHT.
# Muss MANUELL hinzugefügt werden oder Chrome direkt starten:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9999 \
  --remote-allow-origins=* \
  --force-renderer-accessibility \
  --no-first-run \
  --user-data-dir=/tmp/heypiggy-bot-$(date +%s) \
  'URL'
```

---

### §Q9 — Zusammenfassung: Vorher vs. Nachher

| Metrik | Vor diesem Debugging | Nach den 8 Fixes |
|--------|---------------------|-------------------|
| **CDP Target** | Falscher Tab (Dashboard) | ✅ Korrekter Tab (Survey) |
| **Modal Interaktion** | Klicks auf falsche Buttons | ✅ Alle Modals vorher geschlossen |
| **Form Filling** | Felder bleiben leer | ✅ React Native Setter + Events |
| **Sprachauswahl** | Button-Klick (falsch) | ✅ Select.selectedIndex |
| **Balance Reading** | 125.00€ (falsch) | ✅ 2.23€ (korrekt) |
| **Element Targeting** | querySelector (instabil) | ✅ getElementById (stabil) |
| **Click Reliability** | el.click() auf React (fail) | ✅ CDP dispatchMouseEvent |
| **cua-driver AX-Tree** | 0 Elemente (blind) | ✅ 254 Elemente (sichtbar) |