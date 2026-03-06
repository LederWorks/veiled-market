---
name: terraform-import
description: Import existing cloud resources into Terraform / OpenTofu state so they can be managed as code. Generates configuration scaffolding where possible.
platforms: [aws, azure, gcp, oci, digitalocean, vsphere, terraform-cloud]
languages: [hcl, bash]
---

When asked to import existing infrastructure into Terraform / OpenTofu:

## Classic import (all Terraform versions)

```bash
terraform import RESOURCE_ADDRESS RESOURCE_ID
```

Examples:
```bash
terraform import aws_s3_bucket.my_bucket my-existing-bucket-name
terraform import azurerm_resource_group.rg /subscriptions/SUB_ID/resourceGroups/my-rg
terraform import google_compute_instance.vm projects/PROJECT/zones/ZONE/instances/NAME
```

## Native import blocks (Terraform ≥ 1.5 / OpenTofu ≥ 1.6)

Add an `import` block to your configuration:
```hcl
import {
  to = aws_s3_bucket.my_bucket
  id = "my-existing-bucket-name"
}
```
Then run:
```bash
terraform plan -generate-config-out=generated.tf
terraform apply
```
This auto-generates the HCL configuration from the real resource.

## Workflow

1. **Identify the resource type and ID.** Use cloud console or CLI to find the resource ID in the format the provider expects.
2. **Write a skeleton resource block** (or use `-generate-config-out` for Terraform ≥ 1.5).
3. **Run the import command.**
4. **Run `terraform plan`** — it should show zero changes if the configuration matches the live resource.
5. **Adjust the configuration** to eliminate any drift shown in the plan.
6. **Commit the updated `.tf` files** and remove the `import` block after the resource is tracked.

## Finding resource IDs

| Provider | Resource | ID Format |
|----------|----------|-----------|
| AWS | `aws_s3_bucket` | Bucket name |
| AWS | `aws_vpc` | `vpc-XXXXXXXX` |
| Azure | `azurerm_resource_group` | Full ARM resource ID |
| GCP | `google_compute_instance` | `projects/P/zones/Z/instances/N` |
| Kubernetes | `kubernetes_namespace` | `namespace-name` |

## Mass import with Terraformer CLI

For importing many existing resources at once:
```bash
# Install Terraformer
go install github.com/GoogleCloudPlatform/terraformer/...@latest

# Import all AWS VPC resources
terraformer import aws --resources=vpc --regions=us-east-1
```
