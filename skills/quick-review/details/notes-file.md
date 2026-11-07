# Record each pass as it finishes

1. At Pass 0, name a notes file after the tree you are about to review, because a pass that sits only in the context is lost at a handoff:

```bash
key="$(git rev-parse --short HEAD)-$( { git diff HEAD; git status --porcelain; } | shasum | cut -c1-8)"
notes="$(git rev-parse --absolute-git-dir)/quick-review/$key.md"
mkdir -p "$(dirname "$notes")"
```

2. If the file already exists, then read it, keep the passes it records, and run only the ones it lacks.
3. After each pass, append that pass's dispositions, its artifacts, and its candidates to the file before you start the next one.
4. At Classify and Output, read the candidates from the file.
5. When you hand off mid-review, name the file in the handoff.
6. For a staged review ([stages.md](stages.md)), key the file on the merge-base instead, `notes="$(git rev-parse --absolute-git-dir)/quick-review/staged-$(git merge-base HEAD origin/<default_branch> | cut -c1-8).md"`, so it lasts across fixes.
7. Open a staged notes file with the stage plan: each stage's files, its fingerprint, and whether it is done, and record each stage's passes under it; the stage fingerprints decide what carries over.
