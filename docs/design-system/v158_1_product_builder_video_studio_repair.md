# v158.1 - Product Builder and Video Studio Repair

v158.1 removes the remaining technical CRUD windows from trainer product and video workflows.

Updated areas:

- `TrainerProductBuilderDashboard` no longer embeds the old course/program panel and now uses product metrics, product list, editor, readiness and catalog preview as the primary workspace.
- `TrainerUploadPanel` is rebuilt as a premium `Видео и материалы` studio with Russian tabs for videos, programs and bundles.
- Video, program, lesson and bundle editor labels are localized and no longer expose technical phrases such as video asset, storefront, draft editor or raw status labels.
- `/trainer/videos` now renders the premium trainer shell directly around the video/material studio.
- `/trainer/dashboard/products` uses the premium trainer shell copy for product publishing.

Verification:

- `npm run typecheck`
- `npm run test:contracts`
- `git diff --check`

`npm run build` is still blocked in the local workspace by existing `.next/trace` file permissions.
