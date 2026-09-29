# Reading order

## Ten minutes

[README](../README.md) only. The client, the constraint, the scale, the hardships, and the funding order.

## Thirty minutes

1. [README](../README.md)
2. [Privileges](privileges.md) — why a superuser flag and an environment file are different locks.
3. [Database](database.md) — integrity, operations, and overload on a small SQLite site.
4. [Examples index](../examples/README.md) — what each module teaches and whether it shipped.

## The full read

1. [Security](security.md)
2. [Privileges](privileges.md)
3. [Dependencies](dependencies.md)
4. [Languages and translation](translation.md)
5. [Database](database.md)
6. [Design](design.md)
7. [What comes next](what-next.md)

## How each essay is built

Every essay opens with two paragraphs:

- **Shipped** — what the contract actually changed on the live site.
- **Pattern** — the general rule a reader can take to another project.

Every essay ends with a takeout: about fifteen lines of code, labeled **Shipped** or **Recommended**, with a link to the full module in [examples/](../examples/). Recommended code is a pattern the contract did not implement, and the essay says so where it introduces it.
