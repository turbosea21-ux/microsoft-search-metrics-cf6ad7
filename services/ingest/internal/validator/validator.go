// Package validator checks that a raw telemetry event carries the fields the
// downstream pipeline depends on. It is intentionally lenient: only the small
// set of fields metrics and traces actually need is required.
package validator

import (
	"errors"
	"fmt"
)

// Event is the loosely-typed shape we read off the raw topic. We keep it as a
// map so an unexpected producer field doesn't break decoding — validation, not
// the JSON decoder, is the gate.
type Event = map[string]any

var requiredFields = []string{
	"schema_version",
	"event_time",
	"service",
	"endpoint",
	"request_id",
	"trace_id",
	"status_code",
	"latency_ms",
}

// ErrInvalid wraps a human-readable reason; the reason is stored on the DLQ
// record so an operator can triage without re-deriving it.
var ErrInvalid = errors.New("invalid telemetry event")

// Validate returns nil if the event is usable, or an error explaining why not.
func Validate(e Event) error {
	for _, f := range requiredFields {
		if _, ok := e[f]; !ok {
			return fmt.Errorf("%w: missing field %q", ErrInvalid, f)
		}
	}
	if v, ok := e["schema_version"].(float64); !ok || int(v) != 1 {
		return fmt.Errorf("%w: unsupported schema_version", ErrInvalid)
	}
	if code, ok := e["status_code"].(float64); !ok || code < 100 || code > 599 {
		return fmt.Errorf("%w: status_code out of range", ErrInvalid)
	}
	if lat, ok := e["latency_ms"].(float64); !ok || lat < 0 {
		return fmt.Errorf("%w: latency_ms must be a non-negative number", ErrInvalid)
	}
	return nil
}
