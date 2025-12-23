This is a tranformation Lambda for Amazon Data Firehose. It takes a raw CloudTrail
event and performs the following transformations:

* The top-level field names are optionaly transformed to "snake_case" (lowercase words
  separated by underscores).
* All nested JSON objects are stringified, resulting in a single-level JSON object.
* These stringified objects may be optionally truncated, allowing them to fit into
  limited-size database columns.
* Any fields that don't match known CloudTrail fields are optinally discarded,
  avoiding issues if/when AWS adds new fields to the event.

It is used by the CloudTrail firehose examples [here](../cloudtrail_firehose).


## Configuration

Configuration is via environment variables:

* `USE_SNAKE_CASE`: if 1, the top-level field names are transformed to snake_case;
  if 0 or not present, they are left alone.

* `DISCARD_UNKNOWN_FIELDS`: if 1, then any top-level field that isn't in the
  transformation list will be discarded; if 0 or not present, then they will
  be included, _potentially transformed to snake_case_. The former is useful
  when the output must match a table definition, the latter to capture any
  new fields that AWS might add.

* `TRUNCATE_STRINGIFIED_FIELDS` if used, this must contain a numeric value;
  all stringified JSON fields will be truncated to that number of characters.
  This is only required if the destination (such as Redshift) has a limit on
  field size, to avoid exceeding that limit (which the `request_parameters`
  and `response_elements` can do). Beware that enabling this will make any
  truncated fields unparseable as JSON.

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
