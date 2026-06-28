# v160.1 — Integrate Media Picker Into Product Builder

v160.1 completes the product builder integration for the trainer media picker.

## Scope

- Product materials now render the media picker as the main workflow.
- Selected videos remain bridged through `videoIdsText` for the existing backend payload.
- Manual video ID entry remains available only inside the collapsed advanced field.
- `intent=attach-video` highlights the materials section.
- Selected media rows avoid raw IDs and show stable fallback copy.
- Added missing CSS contract for the media picker integration layer.

## Verification

- `npm run typecheck`
- `npm run build`
- `npm run test:contracts`
