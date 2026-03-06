---
name: terraform-apply
description: Apply a Terraform / OpenTofu plan to create, update, or delete infrastructure resources. Always shows a plan summary and requests confirmation before applying.
---

When asked to apply Terraform / OpenTofu changes:

1. **Check for an existing saved plan.** If `tfplan.binary` exists and is recent (< 30 minutes), offer to use it.

2. **Generate a fresh plan if needed.**
   ```bash
   terraform init -input=false
   terraform plan -input=false -out=tfplan.binary 2>&1 | tee tfplan.txt
   ```

3. **Summarise the plan** to the user:
   - Number of resources to add / change / destroy
   - Any destructive actions (highlight in bold / warning)
   - Estimated cost impact if infracost is available

4. **Request explicit confirmation** before proceeding if there are any destructions or if this is a production workspace.

5. **Apply the plan:**
   ```bash
   terraform apply -input=false tfplan.binary 2>&1 | tee tfapply.txt
   ```

6. **Report the outcome:**
   - Resources created / updated / destroyed
   - Any outputs produced
   - Errors encountered (with suggested remediation)

7. **Clean up temporary plan files** after a successful apply:
   ```bash
   rm -f tfplan.binary tfplan.txt tfapply.txt
   ```

## Safety rules

- **Never** run `terraform apply -auto-approve` unless the user has explicitly requested it.
- **Always** run a plan first; never apply from scratch without a prior plan.
- **Lock protection:** if the state is locked by another process, show the lock ID and ask the user before attempting to break it.
- **Workspace check:** confirm the active workspace matches the intended environment (dev/staging/prod).

## Useful flags

- `-target=RESOURCE` — apply only specific resources
- `-parallelism=N` — control concurrency (default 10)
- `-refresh=false` — skip state refresh before apply
- `-var-file=FILE` — use a specific variable file
