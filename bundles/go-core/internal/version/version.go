// Package version records the version of this module.
//
// Go is the odd one out among rhiza's language layers: a Python project keeps its
// version in pyproject.toml and a Rust crate keeps it in Cargo.toml, but a Go
// module's version *is* its git tag — nothing in the source tree carries it, and
// nothing carries it into a built binary either.
//
// So this file is that carrier. `.rhiza/.cfg.toml` points bump-my-version at the
// constant below, which means the release flow rewrites it and creates the
// matching tag in one commit: the two can never disagree. Print it from a
// `--version` flag, stamp it into a build, or ignore it — but do not delete it,
// or the release flow has no version location to write to.
package version

// Version is the module version. bump-my-version rewrites this literal on
// release; the tag it creates is "v" + this value.
const Version = "0.0.0"
