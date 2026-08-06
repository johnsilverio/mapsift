//! Whether two operations meet at all: the pure decision the granularity ladder rests on.
//!
//! Trace: M9 (the conflict unit **is** the target path), T3.1 (different features never conflict,
//! and neither do different properties of one feature), foundation section 4; C2.
//!
//! What the verdict is once two operations do meet belongs to the conflict rule (M13) and is not
//! decided here. The nested case, an ancestor address against a descendant of it, is deferred to
//! the conflict slice with T3.4 (delete against edit), which is where the rule that decides it
//! lands; until then this answers only the same-address question.

use crate::envelope::TargetPath;

/// True when two operations address different conflict units, so neither can contend with the
/// other whatever each of them does (M9, T3.1). The nested case, an ancestor address against a
/// descendant of it, is deferred to T3.4 and is not what this answers (module doc).
pub fn are_disjoint(one: &TargetPath, other: &TargetPath) -> bool {
    one != other
}
