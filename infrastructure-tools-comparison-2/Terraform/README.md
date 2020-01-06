This variant of the project uses Terraform to create resources.

To start, you must [download Terraform for your system](https://www.terraform.io/downloads.html).
If you run Linux, it makes more sense to unpack into `$HOME/bin` rather than install in a system
directory: you'll find that you update the deployment frequently.


Once you've done that, create the resources is a two-step process (both of which must be run from
the child directory):

```
terraform init
```

Will download the AWS provider, and

```
terraform apply
```

Will performs the infrastructure changes. You have to manually approve this step.

It may turn into a three-step process: sometimes the users or groups aren't ready to have roles applied,
and you see an error about the resource not existing. Running `terraform apply` a second time resolves
this.

To destroy the resources:

```
terraform destroy
```

Note that my `.gitignore` file explicitly excludes the `tfstate` files. This is _not_ something that
you'd do in a real deployment; those files should be checked-in alongside the template.
