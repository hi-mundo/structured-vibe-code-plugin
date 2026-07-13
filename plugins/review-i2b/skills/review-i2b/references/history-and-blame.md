# History and Blame

Inspect at least three meaningful revisions for every material path: the review reference and two earlier revisions that illuminate the behavior. More may be required when changes are cosmetic or history is sparse.

## Procedure

1. Establish the comparison reference and record its commit.
2. Use path history with rename detection:

   ```bash
   git log --follow --format='%H%x09%aI%x09%s' -- path
   ```

3. Select revisions by semantic relevance, not merely the previous two commits.
4. Inspect complete changes and nearby contracts:

   ```bash
   git show --find-renames REV -- path
   git blame -w -L START,END REV -- path
   ```

5. Compare intent artifacts, tests, schemas, and callers from the same revisions where available.
6. Record whether each change added, preserved, redirected, or accidentally removed behavior.

## Interpretation rules

- `git blame` reports the last textual change to a line, not the origin of the product decision or defect.
- Refactors, formatting, file moves, generated code, squashes, and cherry-picks weaken attribution.
- SZZ-style reasoning identifies candidate bug-introducing changes; it does not prove causality.
- A repeated pattern may be an intentional invariant, copied defect, compatibility constraint, or convention. Seek independent intent evidence.
- If fewer than three meaningful revisions exist, state the limitation. Do not count irrelevant formatting changes to satisfy the rule.

Use `../../scripts/review_preflight.py` to inventory revision availability. Select and interpret revisions manually.
