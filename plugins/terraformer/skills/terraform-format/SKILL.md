---
name: terraform-format
description: Format Terraform / OpenTofu HCL files to the canonical style using terraform fmt. Supports dry-run checking and recursive formatting.
platforms: [aws, azure, gcp, oci, digitalocean, vsphere, terraform-cloud, github-actions, azure-devops, gitlab-ci, jenkins]
languages: [hcl]
---

When asked to format Terraform / OpenTofu files:

1. **Check-only mode** (default when validating code style — does not modify files):
   ```bash
   terraform fmt -check -recursive -diff 2>&1
   ```
   Display the diff so the user can see what would change.

2. **Format in place** (when the user wants files updated):
   ```bash
   terraform fmt -recursive 2>&1
   ```
   List every file that was reformatted.

3. **Single file formatting** (when working on a specific file):
   ```bash
   terraform fmt <filename.tf>
   ```

4. **Report results:**
   - Files changed (or would change)
   - Confirmation that all files now conform to the canonical style

## What `terraform fmt` fixes

- Indentation (2-space indent)
- Attribute alignment within blocks
- Blank lines between blocks
- Comment style normalisation
- Heredoc indentation

## What `terraform fmt` does NOT check

- Logic errors or invalid references (use `terraform validate`)
- Security issues (use tfsec or checkov)
- Naming conventions (use tflint with a ruleset)

## Pre-commit integration tip

To enforce formatting automatically, add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.96.1
    hooks:
      - id: terraform_fmt
```
