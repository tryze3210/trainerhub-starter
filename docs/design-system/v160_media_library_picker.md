# v160 — Premium Media Library Picker and Product Publishing Flow

v160 closes the trainer product workflow from uploaded video to product publishing without requiring trainers to paste raw video IDs as the main path.

## Scope

- Added `TrainerProductMediaPicker` backed by `uploadApi.listMyVideos()`.
- Added `TrainerSelectedMediaList` for selected product videos.
- Added `TrainerProductAdvancedIdField` for optional manual ID entry.
- Connected product builder materials to the trainer video library.
- Added `intent=attach-video` highlight support for returning from video upload.
- Added a return CTA from saved videos to product builder.
- Simplified video/content rail cards by removing descriptions and full public address strings.

## Verification

- `npm run typecheck`
- `npm run build`
- `npm run test:contracts`
