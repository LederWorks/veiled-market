---
name: terraform-state
description: Inspect and manage Terraform / OpenTofu state. Supports listing, showing, moving, removing, and pulling state entries safely.
---

When asked to manage or inspect Terraform / OpenTofu state:

## Listing state resources

```bash
terraform state list
terraform state list 'module.networking.*'   # filter by prefix
```

## Showing a specific resource

```bash
terraform state show 'aws_instance.web'
```
Displays all attributes of the resource as stored in state.

## Moving a resource (rename / refactor)

```bash
terraform state mv 'aws_instance.old_name' 'aws_instance.new_name'
```
Use this when renaming a resource in configuration without recreating it.
Always run `terraform plan` after to confirm no unintended changes.

## Removing a resource from state (without destroying it)

```bash
terraform state rm 'aws_instance.unmanaged'
```
Use this to stop managing a resource without deleting it from the cloud.
Warn the user that the resource will become unmanaged ("orphaned").

## Pulling raw state

```bash
terraform state pull > terraform.tfstate.backup
```
Useful for inspection or manual editing (requires caution).

## Pushing modified state

```bash
terraform state push terraform.tfstate.modified
```
> ⚠️ Only use in emergencies. Prefer `terraform import` or `state mv` instead.

## Refreshing state

```bash
terraform refresh
```
Or with newer Terraform versions:
```bash
terraform apply -refresh-only
```

## State locking

If a state lock is stuck:
```bash
terraform force-unlock LOCK_ID
```
Only do this after confirming no other process is running against this state.

## Best practices

- Always back up state before manual operations: `terraform state pull > backup.tfstate`
- Use remote state backends (S3, Azure Blob, GCS, Terraform Cloud) for team environments
- Enable state versioning on the backend bucket
- Never commit `terraform.tfstate` to source control — use `.gitignore`
