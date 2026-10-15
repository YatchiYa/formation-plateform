---
name: sheets-formulas
description: Write, debug, optimize or explain advanced Google Sheets formulas (XLOOKUP, QUERY, FILTER, ARRAYFORMULA, LET, LAMBDA/MAP/BYROW, SUMIFS, IMPORTRANGE, dates, text, regex). Load as soon as a formula goes beyond SUM/AVERAGE, a formula returns an error, or the user asks what a formula does.
---
# Google Sheets formulas — expert level

## Rule #1: API syntax
Through the API (sheets_ecrire), formulas are ALWAYS written **in English with commas**, whatever the spreadsheet
language: `=SUMIFS(C:C,A:A,"Lille")`, never `=SOMME.SI.ENS(C:C;A:A;"Lille")`. The user sees them translated in the UI.
When explaining a formula to a French-speaking user, give the French name too (SUMIFS = SOMME.SI.ENS,
XLOOKUP = RECHERCHEX, IF = SI, IFERROR = SIERREUR, COUNTIFS = NB.SI.ENS, TODAY = AUJOURDHUI).

## One formula per column, not one per row
Prefer a single array formula in row 2 that fills the whole column — faster, consistent, extends automatically:
- `=ARRAYFORMULA(IF(A2:A="",,B2:B*C2:C))` — row-by-row math, blank when the row is empty.
- `=MAP(A2:A,B2:B,LAMBDA(a,b,IF(a="",,a&" "&b)))` — richer per-row logic.
- `=BYROW(B2:E,LAMBDA(r,IF(COUNTA(r)=0,,SUM(r))))` — row totals.
- Header + formula in one cell: `={"Margin";ARRAYFORMULA(IF(B2:B="",,(B2:B-C2:C)/B2:B))}` in row 1.
Before writing an array formula, check (sheets_lire) that the target column is EMPTY below it — otherwise
#REF! ("Array result was not expanded because it would overwrite data").

## Lookup
- `=XLOOKUP(key,Ref!A:A,Ref!C:C,"not found")` — replaces VLOOKUP / INDEX-MATCH; exact match by default.
- Multiple criteria: `=XLOOKUP(1,(Ref!A:A=E2)*(Ref!B:B=F2),Ref!C:C,"")`.
- Whole column at once: `=ARRAYFORMULA(IF(A2:A="",,XLOOKUP(A2:A,Ref!A:A,Ref!C:C,"")))`.
- `=FILTER(Sales!A2:F,Sales!C2:C="Lille",Sales!F2:F>100)` — every matching row.
- `=UNIQUE(...)`, `=SORT(range,col,FALSE)`, `=SORTN(range,10,0,3,FALSE)` (top 10 by column 3), `=CHOOSECOLS`, `=VSTACK`, `=HSTACK`.

## QUERY — the spreadsheet's SQL, the most powerful single function
`=QUERY(Sales!A1:F,"select B, sum(E) where C = 'Lille' and E > 0 group by B order by sum(E) desc label sum(E) 'Revenue'",1)`
- Columns by letter (A, B…); with `{}` arrays or IMPORTRANGE, by position: Col1, Col2…
- Strings in single quotes; dates: `where A >= date '2026-01-01'`; last argument = number of header rows.
- `pivot` to cross-tab: `select B, sum(E) group by B pivot D`. `limit 10` for top N. `format E '#,##0'`.
- Dynamic criteria: `"... where C = '"&H1&"'"`.
- A column mixing text and numbers → QUERY keeps the majority type and blanks the rest: clean it first.

## Conditional aggregates
`SUMIFS`, `COUNTIFS`, `AVERAGEIFS`, `MAXIFS`, `MINIFS`. Criteria: `">=100"`, `"<>"` (non-blank), `"*lille*"` (contains),
`">="&DATE(2026,1,1)`. For computed conditions: `=SUMPRODUCT((A2:A="Lille")*(MONTH(B2:B)=10)*C2:C)`.

## LET — readability and performance
`=LET(rev,SUMIFS(E:E,B:B,H2),target,XLOOKUP(H2,Targets!A:A,Targets!B:B),IF(target=0,,rev/target))` — each
sub-calculation computed once, the formula reads like code. Combine with LAMBDA for reusable logic.

## Dates and text
- `TODAY()`, `EOMONTH(d,0)`, `EDATE(d,1)`, `DATEDIF(a,b,"D")`, `NETWORKDAYS(a,b)`, `ISOWEEKNUM(d)`, `TEXT(d,"yyyy-mm")`.
- `REGEXEXTRACT(A2,"\d{5}")`, `REGEXMATCH`, `REGEXREPLACE`, `SPLIT(A2,";")`, `TEXTJOIN(", ",TRUE,range)`, `PROPER`, `TRIM`, `CLEAN`.
- Locale trap: in a fr_FR spreadsheet "12/10/2026" is 12 October; in en_US it is 10 December. Check `locale` in
  sheets_infos. Safest: `=DATE(2026,10,12)` or ISO "2026-10-12".

## Across spreadsheets
`=IMPORTRANGE("url","Tab!A1:F")` — the first time, the user must click "Allow access" in the cell. Wrap in QUERY to filter.

## Performance on big sheets
Avoid volatile functions in thousands of cells (NOW, TODAY, RAND, INDIRECT, OFFSET). Prefer bounded or open-ended
ranges that start at the data (A2:A), one array formula per column, and QUERY/FILTER over many SUMIFS.

## Error diagnosis
- `#N/A`: key not found — stray spaces? text vs number? (TRIM, VALUE, TO_TEXT). Hide only when expected: `IFNA(x,"")`.
- `#REF!`: deleted range, or array formula blocked by filled cells.
- `#VALUE!`: text where a number is expected (imported numbers: `VALUE(SUBSTITUTE(A2,",","."))`).
- `#DIV/0!`: `IF(b=0,,a/b)`. `#NAME?`: misspelled function or French name sent through the API.
- `#ERROR!`: parse error — usually `;` instead of `,` or unbalanced quotes/parentheses.
- Audit with sheets_lire rendu="formules"; never mask errors with IFERROR before understanding them.

## Verify
After writing a formula, re-read the range (rendu="valeurs"): no errors, plausible results, spot-check one row by hand.
