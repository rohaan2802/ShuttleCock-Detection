# Project maintenance

- Keep this repository connected to https://github.com/rohaan2802/ShuttleCock-Detection.git.
- The owner requests that completed, verified changes be committed and pushed to this repository. Never force-push or include unrelated local changes. Report authentication or deployment blockers honestly.
- Update README.md with behavior, setup and deployment changes in the same change. Keep the live link accurate.
- Preserve desktop robotics/CSV features, local Gradio and the static browser app.
- Use ShuttleBotRealtime/models/shuttle_yolov8n_best.pt as the canonical trained checkpoint. Regenerate docs/models/shuttle.onnx and its metadata when that checkpoint changes; verify output parity.
- app.py is the common launcher. GitHub Pages serves docs/ and cannot run Python.
- Run npm test for browser decoder changes and check real model inference when changing exports/preprocessing.
- Never commit credentials, camera captures, or local caches.
