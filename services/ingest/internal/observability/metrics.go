// Package observability exposes Prometheus metrics for the ingest service.
// Label sets are kept deliberately low-cardinality (service/topic/result),
// never per-request ids.
package observability

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	EventsConsumed = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "ingest_events_consumed_total",
		Help: "Raw telemetry events consumed.",
	}, []string{"topic"})

	EventsResult = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "ingest_events_result_total",
		Help: "Outcome of each consumed event.",
	}, []string{"result"}) // result = clean | dlq

	ProcessSeconds = promauto.NewHistogram(prometheus.HistogramOpts{
		Name:    "ingest_process_seconds",
		Help:    "Per-event validate+enrich+publish latency.",
		Buckets: prometheus.DefBuckets,
	})
)

// Serve exposes /metrics for Prometheus to scrape.
func Serve(addr string) {
	go func() {
		mux := http.NewServeMux()
		mux.Handle("/metrics", promhttp.Handler())
		_ = http.ListenAndServe(addr, mux)
	}()
}
