---
name: terraform-plan
description: Preview infrastructure changes by running terraform plan (or tofu plan). Summarises additions, changes, and destructions before any resources are modified.
---

When asked to plan Terraform / OpenTofu changes, follow these steps:

1. **Find the root module.** Look for `main.tf`, `terraform.tf`, or `*.tf` files in the current directory and its parents. If multiple roots exist, ask the user which one to target.

2. **Initialise if needed.**
   ```bash
   if [ ! -d ".terraform" ]; then
     terraform init -input=false
   fi
   ```

3. **Select the correct workspace** if one is specified or discoverable from context.
   ```bash
   terraform workspace select <name>
   ```

4. **Run the plan** with a saved plan file for reproducibility:
   ```bash
   terraform plan -input=false -out=tfplan.binary 2>&1 | tee tfplan.txt
   ```

5. **Parse the plan output.** Count and display:
   - Resources to add (`+`)
   - Resources to change (`~`)
   - Resources to destroy (`-`)
   - Moved / replaced resources

6. **Highlight destructive changes.** Warn explicitly if any resources will be destroyed or replaced.

7. **Security check.** Flag resources that:
   - Grant overly broad IAM permissions (`*`)
   - Disable encryption or public access controls
   - Expose services to `0.0.0.0/0`

8. **Output a summary** to the user before recommending next steps (apply or cancel).

## Useful flags

- `-target=RESOURCE` — plan only specific resources
- `-var-file=FILE` — use a specific variable file
- `-refresh=false` — skip state refresh (faster for large stacks)
- `-compact-warnings` — suppress repetitive warnings

## Exit codes

- `0` — No changes required
- `1` — Error encountered
- `2` — Changes detected (expected for a successful plan with differences)
