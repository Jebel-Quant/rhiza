package version

import (
	"regexp"
	"testing"
)

// WHY THIS FILE EXISTS. Two reasons, and the second is the one that is easy to lose.
//
// It checks a real invariant. `.bumpversion.toml` parses the constant next door with
// this same shape and sets `ignore_missing_version = false`, so a hand-edited
// `const Version = "1.2"` does not fail a gate — it fails the *release*, at the one
// moment nobody wants to debug a regex. Cheaper to catch here.
//
// And it is the only test a freshly synced Go project has. `go test ./...` reports
// "[no test files]" for a package without one and still exits 0, so a new go-local
// repo used to pass `make test` — and therefore `make all` — while running nothing
// at all. Rust never had that problem: `cargo init --lib` leaves an `it_works` test
// behind. `go mod init` creates no Go file whatsoever, so the layer has to bring one.
//
// Replacing it is fine once the project has tests of its own. Deleting it and
// shipping nothing else puts the vacuum back.

// semver is the version shape `.bumpversion.toml` can parse: MAJOR.MINOR.PATCH with
// an optional SemVer pre-release. Kept in step with the `parse` key there, not with
// SemVer at large — the release config is what this guards.
var semver = regexp.MustCompile(`^\d+\.\d+\.\d+(?:-[a-z]+\.\d+)?$`)

func TestVersionIsShapedTheWayTheReleaseFlowExpects(t *testing.T) {
	t.Parallel()

	// Deliberately not compared against a literal: bump-my-version rewrites
	// version.go and nothing else, so asserting the shipped "0.0.0" would turn this
	// red on the project's first release.
	if !semver.MatchString(Version) {
		t.Fatalf("Version = %q, want MAJOR.MINOR.PATCH with an optional -pre.N suffix", Version)
	}
}
