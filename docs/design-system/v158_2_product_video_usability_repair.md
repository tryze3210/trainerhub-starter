# v158.2 - Product / Video Studio Usability Repair

v158.2 focuses on production usability for trainer product creation and video upload.

Updated areas:

- Product builder now links directly to video upload from the hero and material editor.
- Product material entry is no longer presented as the primary raw-ID workflow.
- `/trainer/videos` supports upload-first navigation through `?tab=videos&intent=upload`.
- `TrainerUploadPanel` is now a thin wrapper around `TrainerContentStudio`.
- Video upload has a premium upload card with file selection, file-size display, dropzone styling and step-based upload state.
- Content studio uses split support files for content cards, upload formatting and upload UI.
- Product/video studio CSS includes overflow, wrapping and mobile layout safety.

Verification:

- `npm run typecheck`
- `npm run test:contracts`
- `git diff --check`

`npm run build` remains blocked locally by `.next/trace` file permissions.
