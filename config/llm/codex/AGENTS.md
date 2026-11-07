# Global instructions

For each project look at local AGENTS.md file fir project specific instructions. They usually have higher priority that global instructions.
Also, check for ./AGENTS.LOCAL.MD file - instructions there have even higher priority than in project's AGENTS.md file
(project's AGENTS.md file - team preferences, ./AGENTS.LOCAL.MD - my personal preferences).

---

When asked to sync/update/read/re-read agents.md (may be phrased differently), sync all agents.md files - this one, project's AGENTS.md, 
and ./AGENTS.LOCAL.MD (if exists) and list all them in tree structure and a short summary of new rules applied.

---


## Common between all languages

Put a blank line between logical blocks of code. E.g. for go:

Wrong:
```go
func validateGetList(ctx context.Context, auth auth.IAuth, f dal.Filter) error {
	if auth.HasRole(USER_ROLE_ADMIN) {
		return nil
	}
	if f.LocationId == "" {
		return PanoError(ctx, http.StatusForbidden, "api.pano.forbidden")
	}
	if len(f.Status) == 0 || slices.Contains(f.Status, entries.PanoStatusDraft) {
		return validateOwner(ctx, auth, f.LocationId)
	}
	return nil
}
```

Recommended:
```go
func validateGetList(ctx context.Context, auth auth.IAuth, f dal.Filter) error {
	if auth.HasRole(USER_ROLE_ADMIN) {
		return nil
	}

	if f.LocationId == "" {
		return PanoError(ctx, http.StatusForbidden, "api.pano.forbidden")
	}

	if len(f.Status) == 0 || slices.Contains(f.Status, entries.PanoStatusDraft) {
		return validateOwner(ctx, auth, f.LocationId)
	}

	err := testFunc() 
	if err != nil { // no new line before - error processing related to previous logical block
		return err
	}

	return nil
}
```

---


## GOLANG

Do not add useless comments to go functions. Add them only if they really adds important, not obvious information.


## JS

Do not write `if` in 1 line unless is's very short (under 50 chars, condition itself, not the whole line with whitespaces) 
and placed first in the function.

## CSS/SCSS

Order styles logically:
- first positioning, then margins/paddings, then size, then font, then colors, then other styles.
- css variable usually first, possibly with an empty line.
- mixins and other similar things usually at first, unless should be place in a specific place to keep order correct.

But don't tie too much to this rules. If logically it makes sense to organize them slightly different, it's ok. 
They just should have some logical and consistent order.

## Migrations

For `ALTER TABLE` ALWAYS add timeout:

```sql
SET LOCAL lock_timeout = '5s';
ALTER TABLE table_name ADD COLUMN column_name TYPE;
```

## Unsaved VS Code files

Before editing files, query the live Unsaved Files Bridge for the relevant project and exact planned files:

```sh
node ~/prj/own/other/vscode-unsaved/cli.js --workspace /absolute/project --file relative/path --file another/path
```

Check again immediately before writing. Exit codes: 0 = no exact conflicts, 1 = conflicting unsaved files, 2 = check unavailable/incomplete. Inspect JSON `status` too; never interpret unavailable/partial as clean. Paths are matched canonically across all responding VS Code windows, including inactive tabs.

If `conflictingFiles` is nonempty, pause edits to those files and ask the user to save or resolve their buffers; continue independent work. Do not save, discard, or overwrite unsaved editor changes automatically. If only `unrelatedUnsavedFiles` (or unassigned untitled documents) in the relevant project are dirty, keep working and mention them **in bold in the final response**. Do not warn about known dirty files belonging only to other projects.
