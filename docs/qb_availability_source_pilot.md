# QB availability source pilot

Reviewed: 2026-09-07
Scope: San Francisco, 2025 Weeks 8–11.
Purpose: Assess source usefulness, not model performance.

## Evidence table

Times below reproduce the page display without assuming a timezone.

| Game ID | Displayed publication | Purdy designation | Starter evidence | Source |
|---|---|---|---|---|
| 2025_08_SF_HOU | 2025-10-24 03:05 PM | Out | Purdy excluded; replacement starter not explicitly named in this article | [Week 8 report][w8] |
| 2025_09_SF_NYG | 2025-10-31 02:00 PM | Questionable | Article states the plan is for Mac Jones to start | [Week 9 report][w9] |
| 2025_10_LA_SF | 2025-11-07 02:55 PM | Questionable | Article states the plan is for Mac Jones to start | [Week 10 report][w10] |
| 2025_11_SF_ARI | 2025-11-14; no displayed time | Not established by this source | Video-page description identifies Purdy's return as starter | [Week 11 video page][w11] |

[w8]: https://www.49ers.com/news/lenoir-questionable-purdy-out-vs-texans-injury-report-ahead-of-sfvshou
[w9]: https://www.49ers.com/news/purdy-winters-questionable-vs-giants-injury-report-ahead-of-sfvsnyg
[w10]: https://www.49ers.com/news/bethune-white-questionable-vs-rams-injury-report-ahead-of-larvssf
[w11]: https://www.49ers.com/video/shanahan-provides-final-injury-updates-ahead-of-sfvsaz-purdy-pearsall

## Timestamp and content verification

- These are currently accessible official team pages.
- Their displayed publication dates precede the respective games'
  24-hour cutoffs at the calendar-date level.
- Publication timezones have not been verified.
- No independently archived pre-cutoff page versions have been verified.
- Historical revisions to article text or video descriptions are unknown.
- Week 11 evidence comes from the page description; the video itself
  has not been reviewed.
- Exact publication timestamps in UTC remain unset.
- These records are not yet approved as strict point-in-time backtest inputs.

## Interpretation rules

- "Out" rules out the named player but does not identify the replacement.
- "Questionable" alone does not select a starter.
- An explicit reported starting plan is separate from injury status.
- Missing information remains unknown.
- Actual starters and game outcomes are evaluation labels only.

## Initial finding

Official reports contain information absent from the depth-chart signal:
an explicit exclusion in Week 8, starting plans in Weeks 9–10, and a
return-as-starter description in Week 11.

This is a deliberately selected diagnostic sample. It cannot establish
league-wide coverage or an improvement in prediction accuracy.

## Next verification

Investigate publication metadata and archived versions for these pages.
Preserve unresolved cases rather than filling gaps from actual starters.
Do not change production forecasts.

## JSON-LD metadata inspection

Retrieved locally on 2026-09-07. All timestamps explicitly use UTC.

| Week | datePublished | dateModified |
|---|---|---|
| 8 | 2025-10-24T22:05:45.817Z | 2025-10-24T22:05:45.817Z |
| 9 | 2025-10-31T21:00:00Z | 2025-10-31T21:19:55.17Z |
| 10 | 2025-11-07T22:55:00Z | 2025-11-07T22:54:40.237Z |
| 11 | 2025-11-14T22:10:45Z | 2025-11-14T23:10:45.319Z |

Publication and modification metadata place all four reports before
their respective 24-hour forecast cutoffs.

Week 10 has a metadata ordering inconsistency: modification precedes
publication by 19.763 seconds. Cause unknown.

The metadata resolves publication timestamps in UTC, but does not
independently establish the historical wording. No pre-cutoff archived
versions have been verified.

Classification: publisher-metadata-supported historical evidence;
not independently archive-verified.

## Bounded archive check

On 2026-09-07, archive lookup requests for all four sources failed
through the research tool. No capture timestamps or archived contents
were inspected. This does not establish that archived copies are absent.

Retain the classification:
publisher-metadata-supported historical evidence;
not independently archive-verified.

## Pilot results at actual 24-hour cutoffs

| Game | Cutoff UTC | Evidence interpretation | Recorded starter |
|---|---|---|---|
| 2025_08_SF_HOU | 2025-10-25T17:00:00Z | Purdy ruled out; replacement unresolved | Mac Jones |
| 2025_09_SF_NYG | 2025-11-01T18:00:00Z | Explicit starting plan: Mac Jones | Mac Jones |
| 2025_10_LA_SF | 2025-11-08T21:25:00Z | Explicit starting plan: Mac Jones | Mac Jones |
| 2025_11_SF_ARI | 2025-11-15T21:05:00Z | Explicit starting plan: Brock Purdy | Brock Purdy |

All four reports were eligible under the publisher-metadata timing rule.
All remain archive-unverified. Week 10 retains its metadata-order anomaly.

The depth chart selected Purdy in all four cases. The evidence supplied
two alternative starting plans, supported one existing selection, and
excluded Purdy without inventing a replacement in Week 8.

Nine evidence-loader tests passed. Recorded starters were joined only
for retrospective evaluation.

This selected sample demonstrates source usefulness, not general
accuracy. Production forecasts remain unchanged.