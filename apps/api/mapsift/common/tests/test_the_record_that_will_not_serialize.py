"""The second way to lose a record, which is the one no rule was written against.

Trace: ADR-0011 section 3, its clarification of 2026-08-17 that the gate drops a **field** and
never the record, and the extension of the same day that closes the hole the clarification left
open: the guarantee holds even when an allowlisted field will not serialize, because an encoder
that raises inside the formatter loses the whole record and arrives at exactly the outcome the
gate was forbidden, through the encoder instead of through the gate. PRD N9's acceptance that
every user-visible refusal has a matching record and that a failure with no user-visible signal
and no record fails review: a record lost on the way out breaks both, and breaks them in silence.

**Its own module rather than a case in either suite that reads this path, because neither can
reach this honestly.** Both drive the route, and a request hands the formatter only what this
repository's own code chose to put on a record, so a case posted through the route would pin what
the implementation happens to pass rather than what the ADR guarantees. The guarantee is about any
record that reaches a handler, Django's own and a package written later included, so it is pinned
at the handler the application configured and at nothing narrower.

**Here rather than in `tests/`, because it crosses nothing.** The formatter is `common`'s under
ADR-0011 section 5, and `tests/` at the root holds what crosses packages (ADR-0007 section 6).
"""

import logging
from collections.abc import Sequence

from conftest import (
    EVENT,
    REASON,
    JsonObject,
    the_documents_of,
    the_lines_the_logging_path_would_write,
)

# One of the event names ADR-0011 section 4 closes. A refusal rather than an application,
# because the clause a lost record breaks first is the one about refusals: N9 requires every
# user-visible refusal to have a matching record, and a gate that answers "no record" where the
# path answered a client is the difference between evidence and silence.
A_REFUSAL_THIS_RECORD_NAMES = "request.refused"

# What `str` makes of a container that contains itself, which is Python's own answer and is
# written here as a literal so the expectation comes from somewhere other than the code under
# test. ADR-0011 section 3 fixes the degradation as the value's string form, so this is the
# section's own sentence spelled as a value rather than a second reading of it.
THE_STRING_FORM_OF_A_VALUE_THAT_HOLDS_ITSELF = "[[...]]"


def _a_field_no_encoder_can_walk() -> list[object]:
    """A field that will not serialize, and not merely one whose type is unknown.

    The distinction is the whole case. An unknown type is what a `default` hook exists for, so a
    path that survives one has closed a mechanism rather than the guarantee; a structure that
    refers to itself is refused by the encoder's own walk of the object, before any hook is
    consulted, and takes the record with it. That is the shape ADR-0011 section 3's extension ends
    on, a guarantee stated about one mechanism not being a guarantee about the path.
    """
    holding_itself: list[object] = []
    holding_itself.append(holding_itself)
    return holding_itself


def _a_refusal_record_carrying(reason: object) -> logging.LogRecord:
    """One record as a handler meets it: an allowlisted event and an allowlisted reason.

    The reason is the field this hands the value to because it is the one ADR-0011 section 4
    leaves open **by name**: the field names are closed and what a reason may contain is not, so
    it is where a value nobody anticipated actually arrives.

    Built rather than emitted, because emitting it would ask the question through a logger's own
    error handling, which swallows what the formatter raised and would leave the case unable to
    say whether the record was written or lost.
    """
    return logging.makeLogRecord({EVENT: A_REFUSAL_THIS_RECORD_NAMES, REASON: reason})


def _the_field_each_record_carries(field: str, documents: Sequence[JsonObject]) -> list[object]:
    """One field as each record spells it, an absent one read as None rather than raised on.

    Spelled as `test_the_flush_decision_trail.py` spells it and local for the reason that module
    gives about its own arrangers: the same three lines in two modules is duplication, while a
    second name for one reading would be a second spelling, and only the latter misleads a grep.
    """
    return [document.get(field) for document in documents]


def test_a_record_whose_allowlisted_field_will_not_serialize_is_degraded_rather_than_lost() -> None:
    """ADR-0011 section 3's extension of 2026-08-17, which nothing else pins: a record still
    leaves the path when a field it carries cannot be encoded, with the value degraded to its
    string form.

    **What makes it red:** the encoder raises inside the formatter, so the handler never writes a
    line at all and the whole record is gone, which is the outcome the clarification one paragraph
    above that extension refuses. The gate is not what loses it, which is why a rule written about
    the gate does not cover it and why this case exists.

    **What would pass it dishonestly:** emitting the keys and dropping the field, which the second
    assertion refuses by naming the degraded value; and emitting an empty line or free text, which
    `the_documents_of` refuses by reading rather than shrugging.

    The event is the positive control and it is doing real work: a formatter that answered every
    record it could not encode with a fixed placeholder would satisfy the reason assertion while
    losing the decision the record was about, and the join a support desk starts from with it.

    Both are compared as sets rather than as lists, the shape the failure cases in
    `test_the_flush_decision_trail.py` use for the same reason: the guarantee is owed by every
    handler the application configured, so one of them and three of them agreeing are the same
    answer, while none of them is not, an empty set matching neither expectation."""
    written = the_lines_the_logging_path_would_write(
        _a_refusal_record_carrying(_a_field_no_encoder_can_walk())
    )

    degraded = the_documents_of(written)

    assert set(_the_field_each_record_carries(EVENT, degraded)) == {A_REFUSAL_THIS_RECORD_NAMES}
    assert set(_the_field_each_record_carries(REASON, degraded)) == {
        THE_STRING_FORM_OF_A_VALUE_THAT_HOLDS_ITSELF
    }
