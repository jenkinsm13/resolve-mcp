---
name: markers-to-notes
description: Export all timeline markers from DaVinci Resolve as a structured editorial notes document, grouped by color.
disable-model-invocation: true
---

# /markers-to-notes — Export Markers as Editorial Notes

Read all markers from the current timeline and produce a clean, structured document.

## Workflow

1. Use `resolve_get_timeline_info` to get the timeline name, frame rate, and duration
2. Use `resolve_list_markers` to get all markers with frame, timecode, color, name, note, and custom data
3. Group markers by color using this standard editorial color scheme:

| Color | Meaning |
|-------|---------|
| Red | Fix / Problem / Reshoot needed |
| Yellow | Warning / Needs attention |
| Green | Approved / Selects / Good take |
| Blue | General note / Comment |
| Purple | VFX / Graphics needed |
| Cyan | Audio note / Mix note |
| Pink | Client feedback |
| Orange | Temp / Placeholder |

4. Format as markdown with:
   - Header: timeline name, date, total marker count
   - Sections grouped by color (most urgent first: Red → Yellow → Purple → Cyan → Pink → Orange → Blue → Green)
   - Each marker shows: timecode, name, note text
   - Summary at the bottom: count per color

5. Output the markdown directly to the user. If the user specified a file path, also write it to disk.

## Output Format

```markdown
# Editorial Notes — [Timeline Name]
**Date:** [today]  |  **Markers:** [count]  |  **Duration:** [HH:MM:SS]

## 🔴 Fixes Required (X markers)
- **01:02:15:03** — [name] — [note]
- **01:05:22:10** — [name] — [note]

## 🟡 Needs Attention (X markers)
- **00:45:10:00** — [name] — [note]

## 🟢 Approved (X markers)
- **00:00:00:00** — [name] — [note]

---
**Summary:** X fixes, Y warnings, Z approved, W notes
```

## Example Interactions

User: `/markers-to-notes`
→ Read markers, output formatted editorial notes.

User: `/markers-to-notes save to ~/Desktop/notes.md`
→ Same, but also write the file.
