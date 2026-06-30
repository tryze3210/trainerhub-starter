# v166.3 — Repository Hygiene, Contract Readability and CSS Architecture Prep

## Scope

v166.3 is not a product feature release. It stabilizes repository maintainability after the premium UI hardening block and keeps the production quality gate readable before the next UI architecture step.

The pass keeps backend, API contracts, business logic and UI behavior unchanged. It focuses on documentation readability, contract-test safety and a documented CSS architecture preparation path.

## Why This Was Needed

- README was formally current, but the roadmap and implementation history needed to stay easy to review as real Markdown.
- BUILD_REPORT was too short for a production verification artifact.
- The v166 design documentation needed an explicit maintainability note after the contract-gate repair.
- The design-system contract test was hard to extend safely without clear helper functions and grouped sections.
- `frontend/src/app/globals.css` has become a large stylesheet monolith, so the next step needs a plan before any split.

## Updated Files

- `README.md`
- `BUILD_REPORT.md`
- `docs/design-system/v166_production_visual_hardening.md`
- `docs/design-system/v166_3_repository_hygiene_contract_css_prep.md`
- `frontend/tests/contracts/design-system-contract.test.js`
- `frontend/src/app/globals.css`

## Contract Test Rules

- no empty required fragments.
- no empty forbidden fragments.
- All fragment arrays must pass `assertNonEmptyFragments`.
- Contract sections should be grouped by version or product area.
- Failed contracts must explain the file or area and the missing or forbidden fragment.
- Self-contract checks must protect the contract file from `['']`, `[""]` and empty fragment loops.

## CSS Architecture Prep

- Do not move the entire `globals.css` file at once.
- First add an inventory of stable CSS sections and the routes/classes each section protects.
- Then extract only stable scoped blocks into separate CSS files or modules.
- Preserve import order while extracting.
- Add contract tests for new CSS imports before deleting old blocks.
- Keep public, customer, trainer and admin UI contracts green through every split.

## Verification

```bash
cd frontend
npm run typecheck
npm run test:contracts
npm run build
git diff --check
```

## Known Limitation

Build may fail because of the existing `.next/trace` ownership/cache problem. If build fails for that reason, do not report build passed.
