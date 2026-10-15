# Weekly news update — runbook

This is the procedure the weekly scheduled Claude task follows. Edit it to
change how articles are found, judged or scored; the task reads this file
fresh on every run.

**Output of every run:** at most one pull request against `main` that changes
only `data/news.json`. Nothing goes live until Stefano merges it.

---

## 1. Setup

1. Clone the repo, create a branch `news/YYYY-MM-DD`.
2. Read `data/news.json` (existing articles) and the school list in
   `index.html` (`const SF_SCHOOLS = [ ... ]` — each school's `id` and `name`).
3. If an open PR from an earlier run already exists (branch `news/*`), do not
   open a second one. Report that the earlier PR is still waiting and stop.

## 2. Search window

Look for articles published **since the newest `isoDate` already in
`data/news.json`, minus 14 days** (outlets backdate and search indexes lag).
Never add anything older than 24 months: it would carry no Momentum weight.

## 3. Where to look

Search by school name **and** neighborhood context, since many names are
ambiguous (Presidio, Marina, Roosevelt, Francisco, Hoover, Everett, Aptos,
Gateway, Millennium, Nomad).

Primary outlets (use `allowed_domains` in searches):
sfstandard.com, missionlocal.org, sfexaminer.com, kqed.org,
richmondsunsetnews.com, sfgate.com, abc7news.com, nbcbayarea.com,
cbsnews.com/sanfrancisco, jweekly.com, edsource.org, sfbayview.com.

Also run a few broad sweeps per run: "SFUSD middle school", "San Francisco
K-8", "San Francisco private school", "San Francisco charter school".

Known limits:
- **sfchronicle.com blocks automated reading.** Only add a Chronicle article if
  its school and date can be confirmed from a non-paywalled source; otherwise
  list it under "Couldn't verify" in the PR.
- **thefrisc.com** appears to have stopped publishing in 2026; skip unless a
  search surfaces something new.
- Ignore school websites, rankings sites (Niche, GreatSchools), press releases
  and sponsored "Story Studio" content — only independent journalism counts.

## 4. Verify every candidate (no exceptions)

Open the article itself (WebFetch). Reject it unless **all** are true:
- The page is an article, not a tag page, landing page or search result.
- Headline and publication date are read from the page itself.
- It names at least one school from `SF_SCHOOLS` **at the same campus/grade
  level** (e.g. S.F. Waldorf *High School* is not the K-8; KIPP Bayview
  *Elementary* is not a middle school in our list).
- Its URL and headline are not already in `data/news.json` — including URLs
  listed under any article's `relatedCoverage`.

## 5. Same event, several outlets → one card

If the article covers an event that already has a card (or another new
candidate covers it), **do not add a second card**. Add it to the existing
card's `relatedCoverage` array instead:
`{ "publication": "...", "date": "Mon D, YYYY", "url": "https://..." }`
A follow-up with materially new developments may get its own card but must
reuse the same `storyId` so Momentum counts the story once.

## 6. Labeling

| Field | Rule |
|---|---|
| `scope` | `"school"` only if the article is about specific schools' own conduct, results, programs or incidents. District policy (algebra, schedules, budget, lottery, strike) is `"district"` even when schools are named as examples. |
| `signals` | One per school the article is actually about. **Empty array for district scope.** |
| `sentiment` | `1` positive, `0` mixed / neutral / school was a victim, `-1` negative for the school. Judge the school, not the topic: a school targeted by outside harassment is `0`. |
| `strength` | `1` if the school is the subject; `0.5` if it's a featured example. |
| `note` | One plain sentence explaining the label. |
| `relatedSchoolIds` | Every list school named in the article, even if not scored. |
| `sectorType` | Sector of the main school (`public`, `charter`, `private`). District stories are `public`. |
| `snippet` | 1–2 factual sentences. No adjectives the article doesn't support. |
| `verification` | `"Verified — opened <date>."` (stored, not displayed). |
| `id` | `news_<school-or-topic>_<YYYY>`; must be unique. |

When in doubt between two sentiment values, pick `0` and say why in the PR.
Old incidents newly reported (e.g. a charge for abuse years ago) get
`strength: 0.5` and the note must say when the underlying events happened.

## 7. Write, check, open PR

1. Append new objects to `data/news.json` (keep 2-space JSON formatting).
2. Run `python3 scripts/validate_news.py` — it must report 0 errors.
3. Commit only `data/news.json` and open a PR titled
   `News update: N new articles (YYYY-MM-DD)`. The PR body lists:
   - each added article: school(s), headline, outlet, date, scope, sentiment,
     one-line reason;
   - articles merged into `relatedCoverage`;
   - candidates rejected and why (one line each);
   - "Couldn't verify" items;
   - any school whose Momentum label would change (labels are: Getting
     better, Some good news, Mixed press, Some concerns, Getting worse, or
     no badge; e.g. "Everett: Some good news → Getting better").
4. If nothing new was found, **don't open a PR** — just report "No new
   coverage this week" with the searches that were run.

## 8. Never

- Never push to `main`, edit `index.html`, or change Momentum thresholds.
- Never add an article you could not open.
- Never invent a date, headline or quote.
