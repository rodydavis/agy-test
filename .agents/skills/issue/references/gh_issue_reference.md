# GitHub CLI (`gh`) Issue Reference for `rodydavis/agy-test`

All operations MUST be strictly executed against repository `rodydavis/agy-test`.

---

## 1. Repository Enforcement Flag
Always supply `-R rodydavis/agy-test` to all `gh issue` commands:
```bash
gh issue <command> -R rodydavis/agy-test ...
```

---

## 2. Listing and Querying Issues

### List Open Issues
```bash
gh issue list -R rodydavis/agy-test
```

### List Issues in JSON Format
```bash
gh issue list -R rodydavis/agy-test --json number,title,state,labels,assignees
```

### View Single Issue Details
```bash
gh issue view <issue-number> -R rodydavis/agy-test
```

### Fetch Issue Body Only (Raw Markdown)
```bash
gh issue view <issue-number> -R rodydavis/agy-test --json body --jq .body
```

---

## 3. Creating Issues

### Create with Title and Body File
```bash
gh issue create -R rodydavis/agy-test \
  --title "feat: implement issue management skill" \
  --body-file .agents/skills/issue/templates/issue_template.md
```

### Create with Inline Body and Labels
```bash
gh issue create -R rodydavis/agy-test \
  --title "fix: correct task check logic" \
  --label "bug" \
  --body "## Overview\nFixes issue with task checking."
```

### Create with Media Attached
```bash
gh issue create -R rodydavis/agy-test \
  --title "feat: add screenshot preview" \
  --body-file issue_body.md \
  --attach "./preview.png#Preview Screenshot"
```

---

## 4. Updating Issues & Task Checklists

### Edit Body Directly
```bash
gh issue edit <issue-number> -R rodydavis/agy-test --body-file <updated-body.md>
```

### Add or Remove Labels
```bash
gh issue edit <issue-number> -R rodydavis/agy-test --add-label "in-progress" --remove-label "todo"
```

### Post a Progress Comment
```bash
gh issue comment <issue-number> -R rodydavis/agy-test --body-file <progress-comment.md>
```

---

## 5. Attaching Media (Images & Videos)

GitHub CLI natively supports attaching images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) and videos (`.mp4`, `.mov`, `.webm`):
- Format: `--attach '<path_to_file>#<Alt Text>'`
- Multiple files: Repeat `--attach` (up to 50 files).
- When the body references the file as `![Alt Text](./path_to_file.png)`, `gh` replaces the relative path with the GitHub uploaded CDN asset URL automatically.

### Example: Attaching to Existing Issue
```bash
gh issue edit <issue-number> -R rodydavis/agy-test \
  --attach "./artifacts/screenshot.png#Verification Screenshot"
```

### Example: Attaching to a Comment
```bash
gh issue comment <issue-number> -R rodydavis/agy-test \
  --body "Attached demo of completed functionality:" \
  --attach "./demo.mp4"
```

---

## 6. Closing Issues with Pushed Commits

### 1. Close via Commit Message Keywords
Commit messages pushed to the default branch automatically close linked issues when using GitHub keywords:
- `Fixes #<number>`
- `Closes #<number>`
- `Resolves #<number>`

Example:
```bash
git commit -m "feat: complete issue tracking skill

Closes #1"
git push origin master
```

### 2. Explicit CLI Close after Push
```bash
COMMIT_SHA=$(git rev-parse --short HEAD)
gh issue close <issue-number> -R rodydavis/agy-test \
  --reason "completed" \
  --comment "Resolved in commit ${COMMIT_SHA}. Pushed to origin."
```

### 3. Verify Status
```bash
gh issue view <issue-number> -R rodydavis/agy-test --json number,title,state,stateReason
```
