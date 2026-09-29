"""Write machine translation only into empty fields.

Status: shipped (policy). The live management command walks the translated
models and applies exactly this rule per field.

Constraint: an editor may already have written the English or Kazakh text by
hand. A batch job must never be able to overwrite that work, no matter which
backend it uses or how many times it runs.

Failure it prevents: a rerun of the translation job replacing a human
translation with machine output, and the stub backend writing placeholder
copy into live columns.

Refuses to include: the site's model and field list. The batch runs on a copy
of the database, after a backup, in a maintenance window. It never runs inside
the process that serves public pages.
"""


def is_empty(value):
    return value is None or not str(value).strip()


def fill_empty_fields(obj, fields, translate, source="ru", targets=("en", "kk"), dry_run=False):
    """Fill `<field>_<lang>` from `<field>_<source>` where the target is empty.

    `translate(text, source, target)` returns a string, or None to mean
    "no translation available"; None writes nothing.

    Returns (filled, skipped): attribute names written, and attribute names
    left alone because they already held text.
    """
    filled, skipped = [], []
    for field in fields:
        source_value = getattr(obj, f"{field}_{source}", None)
        if is_empty(source_value):
            continue
        for lang in targets:
            if lang == source:
                continue
            attr = f"{field}_{lang}"
            if not hasattr(obj, attr):
                continue
            if not is_empty(getattr(obj, attr)):
                skipped.append(attr)
                continue
            if dry_run:
                filled.append(attr)
                continue
            translated = translate(str(source_value), source, lang)
            if is_empty(translated):
                continue
            setattr(obj, attr, translated)
            filled.append(attr)
    return filled, skipped
