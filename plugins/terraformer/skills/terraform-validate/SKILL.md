---
name: terraform-validate
description: Validate Terraform / OpenTofu configuration files for syntax correctness and internal consistency. Does not require cloud credentials.
platforms: [aws, azure, gcp, oci, digitalocean, vsphere, terraform-cloud, github-actions, azure-devops, gitlab-ci, jenkins]
languages: [hcl, bash]
---

When asked to validate Terraform / OpenTofu configuration:

1. **Initialise the module** (validate needs providers but not credentials):
   ```bash
   terraform init -backend=false -input=false 2>&1
   ```

2. **Run validation:**
   ```bash
   terraform validate -json 2>&1 | tee validate.json
   ```

3. **Parse the JSON output** and report:
   - `valid: true` → display a success message
   - `valid: false` → display each error with:
     - File path and line number
     - Error summary and detail
     - Suggested fix where possible

4. **Run format check** as part of validation:
   ```bash
   terraform fmt -check -recursive 2>&1
   ```
   Report any files that need formatting.

5. **Run tfsec / checkov if available** for security linting:
   ```bash
   which tfsec >/dev/null 2>&1 && tfsec . --format=json 2>&1
   which checkov >/dev/null 2>&1 && checkov -d . --output json 2>&1
   ```

6. **Report a combined summary:**
   - Syntax / config errors
   - Format violations
   - Security findings (HIGH / CRITICAL)

## Common validation errors and fixes

| Error | Likely cause | Fix |
|-------|-------------|-----|
| `Reference to undeclared resource` | Typo in resource address | Check `type.name` spelling |
| `Unsupported argument` | Provider schema mismatch | Check provider version or argument name |
| `Missing required argument` | Required attribute missing | Add the attribute or use a variable |
| `Cycle detected` | Circular dependency | Review depends_on and resource references |
| `Invalid template interpolation` | Malformed `${}` | Check HCL interpolation syntax |
