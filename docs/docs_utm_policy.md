# UTM Policy

## Purpose
UTM parameters make campaign performance attributable across ad platforms, web analytics, and CRM.

## Required parameters (all links)
- `utm_source`: platform or referrer (e.g., `google`, `meta`, `linkedin`, `newsletter`)
- `utm_medium`: channel type (e.g., `cpc`, `paid_social`, `email`, `affiliate`)
- `utm_campaign`: campaign identifier (see Naming Conventions)
- `utm_content`: ad/creative identifier (recommended for paid; required when multiple creatives share the same landing page)
- `utm_term`: optional; use for keyword theme (search) or audience segment (paid social)

## Formatting rules
- Lowercase only
- Use hyphens `-` as separators; no spaces
- Do not include PII in any UTM (no emails, names, phone numbers)

## Examples
- `?utm_source=google&utm_medium=cpc&utm_campaign=2026q1-brand-search&utm_content=rsas-v1&utm_term=brand`
- `?utm_source=meta&utm_medium=paid_social&utm_campaign=2026q1-prospecting&utm_content=vid-15s-v3&utm_term=lookalike-1p`

## QA checklist
Before launching:
1. Click final URLs from the ad preview
2. Confirm UTMs appear in the landing page URL
3. Confirm analytics receives the UTMs (real-time view)
4. Confirm CRM fields map UTMs correctly (lead record)