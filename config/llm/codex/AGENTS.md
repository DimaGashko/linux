# Global instructions

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

	return nil
}
```

---


## GOLANG

Do not add useless comments to go functions. Add them only if they really adds important, not obvious information.

## JS

Do not write `if` in 1 line unless is's very short (under 50 chars, condition itself, not the whole line with whitespaces) 
and placed first in the function.

## Migrations

For `ALTER TABLE` ALWAYS add timeout:

```sql
SET LOCAL lock_timeout = '5s';
ALTER TABLE table_name ADD COLUMN column_name TYPE;
```
