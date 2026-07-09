// Package enrich annotates a validated event with fields the producer cannot
// know (ingest_time) and normalizes loose fields (error_type) so downstream
// consumers see a consistent shape.
package enrich

import (
	"time"

	"github.com/example/search-metrics/ingest/internal/validator"
)

// known maps producer error strings to a small, stable vocabulary. Anything
// unrecognized collapses to "internal" so the metrics dimension stays bounded.
var known = map[string]string{
	"timeout":    "timeout",
	"downstream": "downstream",
	"validation": "validation",
	"internal":   "internal",
}

// Enrich mutates the event in place and returns it.
func Enrich(e validator.Event, now time.Time) validator.Event {
	e["ingest_time"] = now.UTC().Format(time.RFC3339Nano)

	switch raw := e["error_type"].(type) {
	case string:
		if norm, ok := known[raw]; ok {
			e["error_type"] = norm
		} else {
			e["error_type"] = "internal"
		}
	default:
		// nil or absent: a successful request has no error_type.
		e["error_type"] = nil
	}
	return e
}
