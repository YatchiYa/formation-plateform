---
name: sheets-lossless-cleanup
description: Clean, deduplicate, normalize, restructure or merge data WITHOUT erasing anything (this agent cannot delete) — using computed columns, clean tabs, sorting, filters and flags. Load for any cleanup, duplicates, data-quality or standardization request, and for ANY request to "delete" or "remove" something.
---
# Cleaning without losing anything

This agent cannot delete or clear. That is a strength: the original data stays intact and every step is
auditable and reversible. Principle: **raw data stays, the clean version lives next to it**.

## When the user asks to "delete"
Say in one sentence that you don't delete, then offer the best alternative:
- Unwanted rows → a "To delete" column (TRUE) + a filter or filter view that hides them; the user can then delete
  them in two clicks (filter TRUE, select, delete rows). Offer to set this up.
- Unused columns / tabs → hide them (hiddenByUser / hidden).
- Duplicates → a "Deduplicated" tab with `=UNIQUE(Data!A1:F)` (or `=SORTN(Data!A2:F,9^9,2,1,TRUE)` to dedupe on
  key column 1), + conditional formatting that highlights duplicates in the source.
- Wrong value → write the correct value (sheets_ecrire, with confirmation), never an emptied cell.

## Clean tab (recommended)
New tab "Clean data", one array formula per column:
- Spaces / invisible chars: `=ARRAYFORMULA(IF(A2:A="",,TRIM(CLEAN(A2:A))))`; case: `PROPER` / `UPPER`.
- Numbers stored as text: `=ARRAYFORMULA(IF(B2:B="",,VALUE(SUBSTITUTE(SUBSTITUTE(B2:B," ",""),",","."))))`.
- Text dates "12/10/2026": `=ARRAYFORMULA(IF(C2:C="",,DATE(RIGHT(C2:C,4),MID(C2:C,4,2),LEFT(C2:C,2))))`.
- Postcodes / IDs losing leading zeros: `TEXT(A2,"00000")`; phone/email extraction: `REGEXEXTRACT`.
- Inconsistent labels ("Lille", "LILLE", "lille ") → a mapping table + XLOOKUP, or `PROPER(TRIM())`.
- Filtered and sorted in one go: `=SORT(FILTER(Data!A2:F,Data!F2:F<>"Cancelled"),2,TRUE)`.
Then run sheets_profil on the clean tab to PROVE the result (blanks, duplicates, types).

## Merging tabs or files
`={January!A2:F;February!A2:F;March!A2:F}` stacks tabs with the same column layout; drop blank rows with
`=QUERY({January!A2:F;February!A2:F},"select * where Col1 is not null",0)`. Add a source column if needed:
`={ARRAYFORMULA(IF(January!A2:A="",,"January")),January!A2:F}`.
Other spreadsheet: IMPORTRANGE (the user clicks "Allow access" once).

## Sort, filter, reorganize
- sortRange (row order only, nothing lost); setBasicFilter; addFilterView (named personal view, doesn't disturb others).
- Reorder columns: moveDimension. Add a column in the middle: insertDimension.

## Data-quality report (offer it)
Per column: % filled, invalid values, duplicates, outliers — from sheets_profil — as a short table, plus the fix
applied for each issue.

## Always
State before/after in numbers ("1,240 rows, 37 duplicates, 12 unreadable dates → fixed in tab Clean data") and
give the link.
