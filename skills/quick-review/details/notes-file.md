# Record each pass as it finishes

A session can hand off in the middle of a review, and a pass that only sits in the context is gone when it does. At Pass 0, name a notes file after the tree you are about to review:

```bash
key="$(git rev-parse --short HEAD)-$( { git diff HEAD; git status --porcelain; } | shasum | cut -c1-8)"
notes="$(git rev-parse --absolute-git-dir)/quick-review/$key.md"
mkdir -p "$(dirname "$notes")"
```

If the file already exists, a session before you reviewed this same tree: read it, keep the passes it records, and run only the ones it lacks. After each pass, append that pass's dispositions, its artifacts, and its candidates to the file before you start the next one. Classify and Output read the candidates from the file, so a pass that an earlier session ran still reaches the final block.

The file sits inside the git directory, so nothing stages it, and each worktree gets its own. Any edit to the tree changes the key, so no recorded pass carries over onto code it never read. When you hand off mid-review, name the file in the handoff.

For a staged review ([stages.md](stages.md)), key the file on the merge-base instead, `notes="$(git rev-parse --absolute-git-dir)/quick-review/staged-$(git merge-base HEAD origin/<default_branch> | cut -c1-8).md"`, so it lasts across fixes. Open it with the stage plan: each stage's files, its fingerprint, and whether it is done. Under each stage, record its passes the way this file records them for a whole review. The stage fingerprints, rather than the file's name, decide what carries over.
