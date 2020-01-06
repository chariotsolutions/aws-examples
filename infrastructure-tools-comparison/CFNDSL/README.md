This variant of the project uses the CFNDSL Ruby gem to create resources. I include this as an
example of pre-CDK programmatic template generation; at this time I would not recommend using 
it unless you are already a Ruby shop.

You first need to install CFNDSL per the instructions [here](https://www.rubydoc.info/gems/cfndsl)
(and you may also need to install a compatible Ruby version as well).

Then, generate the template using this command:

```
cfndsl --disable-binding -f yaml script.rb > template.yml
```

* `--disable-binding` suppresses a warning about locally-defined configuration.
  In normal use, you would provide the lists of users, groups, &c via external
  configuration files.
* `-f yaml` specifies that the output should be [YAML](https://yaml.org/).
  Omit to generate JSON (in which case you probably want to add `-p`, for
  pretty-printing).

Once you have the template, you can use the AWS Console or CloudFormation CLI to create and
destroy the stack (CFNDSL doesn't let you deploy/undeploy directly).
