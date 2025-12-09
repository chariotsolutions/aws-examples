This is a tranformation Lambda for Amazon Data Firehose, which takes a raw CloudTrail
event and performs the following transformations:

* All nested JSON objects are stringified, resulting in a single-level JSON object.
* The top-level field names are optionaly transformed to "snake_case" (lowercase words
  separated by underscores).

It is used in several of the CloudTrail firehose examples.


## Configuration

Configuration is via environment variables:

* `USE_SNAKE_CASE`: if 1, the top-level field names are transformed to snake_case;
  if 0 or not present, they are left alone.
* `DISCARD_UNKNOWN_FIELDS`: if 1, then any top-level field that isn't in the
  transformation list will be discarded; if 0 or not present, then they will
  be included, _potentially transformed to snake_case_. The former is useful
  when the output must match a table definition, the latter to capture any
  new fields that AWS might add.

Note: for known fields, the transformation to snake_case is table-driven. For
unknown fields, it uses a regex that may fail in corner cases.

Note also that the transformation to snake_case is _not_ recursive. Nested
objects retain their original keys.


## Deployment

The Lambda implementation is contained within the file `index.py`. For a production
deployment, this should be copied verbatim into CloudFormation, or referenced from
Terraform. For the examples that use this transformation, you will need to copy it
manually.

There is also a test class, `tests.py`; this uses the standard Python test module,
and so does not require any dependencies.

```
python tests.py
```
