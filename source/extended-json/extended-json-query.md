# Extended JSON Query

## Abstract

Extended JSON query variation is a superset of Extended JSON. It is
intended to be used for serializing queries that can be specified in
the mongo shell. It supplements the Extended JSON syntax with support
for the following features:

- Trailing commas after the last value in an object

- NumberLong values in quotation marks (aka "double quote")
  - Apostrophe (aka "single quote") is not supported

- Dates constructed with `new Date()` including an `ISODate` format
  - Including support for pre-epoch dates

- Regex pattern enclosed in slashes

## Examples

### Trailing Comma
    The following example shows an example of a JSON object with a trailing comma after the `b: 2` element. The trailing comma is supported only in objects, not in arrays. This is convenient when manually editing the text representation.
```javascript
{$match:
 {a: 1,
  b: 2,}
}
```

### Quoted NumberLong Value
    The EJSON syntax supports a `NumberLong()` constructor but the argument must not be quoted. The following example shows the quoted version of the number.
```javascript
{$match:
 {num:
  {$gt: NumberLong("123456789")}
 }}
```

### Date Constructor
    The following example shows construction of a Date object with the date string represented in ISODate form.
```javascript
{$match:
 {dateField:
  {$lt: new Date("2019-10-23T08:58:17.868Z")}
 }}
```

### Regex Pattern in Slashes
    The following example shows a regex value enclosed in slashes. This is consistent with the MQL syntax.
```javascript
{$regexFindAll:
 {input: \"$obj.obj.obj.obj.str\",
  regex: /transparent|Forward/}
}
```
