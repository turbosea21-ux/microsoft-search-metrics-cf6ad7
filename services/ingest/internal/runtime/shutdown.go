// Package runtime provides graceful-shutdown plumbing: a context that cancels
// on SIGINT/SIGTERM and a helper to run cleanup with a bounded grace period.
package runtime

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"time"
)

// SignalContext returns a context cancelled on SIGINT/SIGTERM, plus a stop func.
func SignalContext() (context.Context, context.CancelFunc) {
	return signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
}

// Shutdown runs cleanup with a hard deadline so a stuck close can't hang the
// process forever. If cleanup overruns the grace period we give up and exit.
func Shutdown(grace time.Duration, cleanup func(context.Context) error) error {
	ctx, cancel := context.WithTimeout(context.Background(), grace)
	defer cancel()

	done := make(chan error, 1)
	go func() { done <- cleanup(ctx) }()

	select {
	case err := <-done:
		return err
	case <-ctx.Done():
		return ctx.Err() // grace period expired
	}
}

// Drain stops accepting new work and waits for in-flight items to finish,
// bounded by the shutdown context. It is the backpressure-respecting exit.
func Drain(ctx context.Context, inflight <-chan struct{}) {
	for {
		select {
		case <-ctx.Done():
			return
		case _, ok := <-inflight:
			if !ok {
				return // all in-flight work drained
			}
		}
	}
}
