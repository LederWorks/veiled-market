---
name: terraform-workspace
description: Manage Terraform / OpenTofu workspaces to support multiple environments (dev, staging, prod) from a single configuration.
---

When asked to manage Terraform / OpenTofu workspaces:

## List workspaces

```bash
terraform workspace list
```
The current workspace is prefixed with `*`.

## Create a new workspace

```bash
terraform workspace new staging
```
This creates a new, empty state and switches to it.

## Select an existing workspace

```bash
terraform workspace select prod
```

## Show current workspace

```bash
terraform workspace show
```

## Delete a workspace

```bash
terraform workspace delete staging
```
> ⚠️ Only possible if the workspace state is empty. Run `terraform destroy` first.

## Workspace-aware configuration patterns

Use `terraform.workspace` in your HCL to vary behaviour per environment:

```hcl
locals {
  env = terraform.workspace

  instance_type = {
    default = "t3.micro"
    staging = "t3.small"
    prod    = "t3.large"
  }
}

resource "aws_instance" "web" {
  instance_type = local.instance_type[local.env]
}
```

Or use per-workspace variable files:
```bash
terraform apply -var-file="envs/${terraform.workspace}.tfvars"
```

## Variable files per workspace

Maintain separate tfvars files:
```
envs/
  dev.tfvars
  staging.tfvars
  prod.tfvars
```

Apply the right one:
```bash
terraform apply -var-file="envs/$(terraform workspace show).tfvars"
```

## Workspace vs. separate state backends

| Approach | Best for |
|---------|---------|
| Workspaces | Similar environments, same configuration |
| Separate root modules | Drastically different environments |
| Terragrunt | DRY multi-environment management at scale |

## Safety tips

- Always run `terraform workspace show` before any plan/apply to confirm the active environment.
- Use CI/CD to enforce workspace selection via environment variables.
- Consider naming workspaces consistently: `dev`, `staging`, `prod`.
