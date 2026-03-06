---
name: terraform-destroy
description: Destroy Terraform / OpenTofu managed infrastructure. Always generates a destroy plan and requires explicit confirmation before proceeding.
platforms: [aws, azure, gcp, oci, digitalocean, vsphere, terraform-cloud, hcp-vault]
languages: [hcl, bash]
---

When asked to destroy Terraform / OpenTofu infrastructure:

> ⚠️ **Destructive operation.** This will permanently delete real infrastructure resources.

1. **Confirm the target.** Before doing anything else, clarify with the user:
   - Which workspace / environment is targeted
   - Whether a partial destroy is intended (specific resources via `-target`)
   - Whether they understand this will delete real resources

2. **Generate a destroy plan first:**
   ```bash
   terraform init -input=false
   terraform plan -destroy -input=false -out=tfdestroy.binary 2>&1 | tee tfdestroy.txt
   ```

3. **Display the full list** of resources to be destroyed. Group by resource type and highlight any:
   - Databases or stateful services
   - IAM roles / policies
   - Network infrastructure (VPCs, subnets)
   - Any resource with downstream dependencies

4. **Require explicit confirmation.** State clearly: "This will destroy N resources. Type `yes` to confirm."

5. **Execute the destroy** only after confirmation:
   ```bash
   terraform apply -input=false tfdestroy.binary 2>&1
   ```

6. **Report outcome:**
   - Resources successfully destroyed
   - Any errors (with remediation steps)
   - Remaining resources (if partial destroy)

7. **Clean up plan files:**
   ```bash
   rm -f tfdestroy.binary tfdestroy.txt
   ```

## Targeted destroy

To destroy a single resource:
```bash
terraform destroy -target=aws_instance.example -input=false
```

## Safety checklist before destroy

- [ ] You are on the correct workspace (not production accidentally)
- [ ] Backups or snapshots exist for any stateful resources
- [ ] Dependent systems have been gracefully shut down
- [ ] The Terraform state lock is not held by another process
