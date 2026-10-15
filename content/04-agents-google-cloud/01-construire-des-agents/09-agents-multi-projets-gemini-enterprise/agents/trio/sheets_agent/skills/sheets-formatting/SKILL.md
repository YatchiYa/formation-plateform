---
name: sheets-formatting
description: Ready-to-use batchUpdate recipes for sheets_modifier — number formats (€, %, dates), conditional formatting (colors, color scales, formula rules), dropdowns and validation, borders, column widths, freezing, protection, named ranges, row groups. Load before any formatting beyond sheets_embellir.
---
# Professional formatting (sheets_modifier)

Always call sheets_infos first (sheetId). A GridRange uses 0-based indexes, start inclusive, end exclusive.
Rows 2 to 100 of column C: `{"sheetId": S, "startRowIndex": 1, "endRowIndex": 100, "startColumnIndex": 2, "endColumnIndex": 3}`.
Omit endRowIndex = to the bottom. Send ALL requests in ONE call (atomic, faster, one version-history entry).
`fields` must list EVERY property you set, and only those — anything listed but not set is reset.

## Number formats (repeatCell, fields "userEnteredFormat.numberFormat")
- Euros: `{"type": "CURRENCY", "pattern": "#,##0.00 [$€-40C]"}` · Integer: `{"type": "NUMBER", "pattern": "#,##0"}`
- Percent: `{"type": "PERCENT", "pattern": "0.0%"}` · Date: `{"type": "DATE", "pattern": "dd/mm/yyyy"}`
- Negatives in red: `{"type": "NUMBER", "pattern": "#,##0;[Red]-#,##0"}` · Thousands: `"#,##0,\"k\""`
```json
{"repeatCell": {"range": R, "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}},
 "fields": "userEnteredFormat.numberFormat"}}
```
Other useful fields: `textFormat.bold`, `textFormat.fontSize`, `horizontalAlignment` (CENTER/RIGHT),
`wrapStrategy` (WRAP), `backgroundColor` ({"red":1,"green":0.9,"blue":0.9}, values 0 to 1).

## Conditional formatting
Value rule: `{"addConditionalFormatRule": {"index": 0, "rule": {"ranges": [R], "booleanRule": {"condition":
{"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]}, "format": {"textFormat": {"foregroundColor": {"red": 0.8}}}}}}}`
Types: NUMBER_GREATER, NUMBER_BETWEEN, TEXT_CONTAINS, TEXT_EQ, DATE_BEFORE, BLANK, NOT_BLANK, CUSTOM_FORMULA.
Whole row driven by one column: CUSTOM_FORMULA `=$F2="Late"` on range A2:H (anchor the column with $, not the row).
Duplicates: CUSTOM_FORMULA `=COUNTIF($A$2:$A,$A2)>1`. Overdue: `=AND($D2<>"",$D2<TODAY(),$E2<>"Done")`.
Color scale: `"gradientRule": {"minpoint": {"color": {"red":0.96,"green":0.8,"blue":0.8}, "type": "MIN"},
"midpoint": {"color": {"red":1,"green":1,"blue":0.8}, "type": "PERCENTILE", "value": "50"},
"maxpoint": {"color": {"red":0.8,"green":0.93,"blue":0.8}, "type": "MAX"}}`.
Palette that stays readable: green {0.8,0.93,0.8}, amber {1,0.95,0.8}, red {0.96,0.8,0.8}; dark text on light fills.

## Dropdowns and input control (setDataValidation, ALWAYS with "rule")
`{"setDataValidation": {"range": R, "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": "To do"},
{"userEnteredValue": "In progress"}, {"userEnteredValue": "Done"}]}, "showCustomUi": true, "strict": true}}}`
From a range: `ONE_OF_RANGE` with `"=Lists!A2:A"`. Checkboxes: `BOOLEAN`. Valid dates: `DATE_IS_VALID`.
Bounded number: `NUMBER_BETWEEN` [0, 100]. Add `"inputMessage"` to guide the user.

## Structure
- Freeze: `updateSheetProperties` `{"properties": {"sheetId": S, "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 1}},
  "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}`.
- Rename / tab color: fields `title` / `tabColorStyle`. Hide a tab (the alternative to deleting it): `hidden`.
- Width: `updateDimensionProperties` `{"range": {"sheetId": S, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
  "properties": {"pixelSize": 220}, "fields": "pixelSize"}`; hide columns: `"hiddenByUser": true`, fields `hiddenByUser`.
- Fit to content: `autoResizeDimensions`. Insert: `insertDimension` (inheritFromBefore). Grow the grid: `appendDimension`.
- Collapsible row/column groups: `addDimensionGroup`. Reorder columns: `moveDimension`.
- Borders: `updateBorders` with top/bottom/left/right/innerHorizontal/innerVertical `{"style": "SOLID", "color": {...}}`.
- Named range: `addNamedRange` `{"namedRange": {"name": "Targets", "range": R}}` → readable formulas (`=SUM(Targets)`).
- Protect (warning only, the owner can still edit): `addProtectedRange` `{"protectedRange": {"range": R,
  "description": "Formulas", "warningOnly": true}}`. Protect formula columns and headers in shared trackers.
- Merge: only when at most ONE cell is filled (otherwise refused — merging destroys the other values). For a
  centered title, merge the filled title cell with empty cells to its right.

## House style for professional sheets
Header: dark fill, white bold text, frozen. Numbers right-aligned with thousands separators; currencies and
percentages formatted; dates in one format. Alternating bands, a filter, columns fitted. No more than 3 accent
colors. Inputs (editable) vs. formulas (protected) visually distinct, e.g. light-yellow fill for input cells.

## Impossible here (by design)
Deleting rows / columns / tabs / rules, clearing cells, copy-paste, find-and-replace.
Offer instead: hide, move (moveDimension), flag (a "Status" column), or let the user do it.
