# GitHub 연구 결과 누적 방법

- Remote: `jiae-jeong/lotto-data`, branch `main`.
- Framework path: `research/expansion_framework_v1/`.
- New study path: `research/expansion_framework_v1/studies/study_batch_XXX/`.
- Preserve existing research files. Add each new batch as new files and commit it with a descriptive message.
- This Codex workspace is not a Git checkout. The initial upload was committed through the connected GitHub integration, without initializing Git in or modifying the local research directory. For later batches, use the GitHub integration to add only new paths, or clone the repository into a separate checkout before using local Git.
- `UPLOAD_SHA256_MANIFEST.csv` records SHA-256 and byte length for the framework files in this upload, excluding the manifest itself.
- Exclude raw source data, caches, compiled Python files, and final-number operating outputs from research uploads unless a separate instruction explicitly includes them.
