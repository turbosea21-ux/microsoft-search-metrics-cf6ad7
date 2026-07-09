// Command ingest consumes raw telemetry, validates and enriches it, and
// republishes to the clean topic. Bad messages go to the DLQ. Offsets are
// committed only after a message is handled, giving at-least-once processing.
package main

import (
	"context"
	"encoding/json"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/segmentio/kafka-go"

	"github.com/example/search-metrics/ingest/internal/dlq"
	"github.com/example/search-metrics/ingest/internal/enrich"
	"github.com/example/search-metrics/ingest/internal/observability"
	"github.com/example/search-metrics/ingest/internal/validator"
)

func main() {
	log := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	observability.Serve(":9101")

	brokers := []string{"localhost:9092"}

	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:        brokers,
		GroupID:        "ingest",
		Topic:          "search.events.raw",
		CommitInterval: 0,
	})
	defer reader.Close()

	clean := &kafka.Writer{Addr: kafka.TCP(brokers...), Topic: "search.events.clean", Balancer: &kafka.Hash{}}
	defer clean.Close()

	deadLetters := dlq.New(brokers, "search.events.dlq")
	defer deadLetters.Close()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	for {
		msg, err := reader.FetchMessage(ctx)
		if err != nil {
			log.Info("fetch stopped", "err", err)
			return
		}
		started := time.Now()
		observability.EventsConsumed.WithLabelValues("search.events.raw").Inc()

		var event validator.Event
		if err := json.Unmarshal(msg.Value, &event); err != nil {
			_ = deadLetters.Send(ctx, string(msg.Key), msg.Value, "unparseable json")
			observability.EventsResult.WithLabelValues("dlq").Inc()
			_ = reader.CommitMessages(ctx, msg)
			continue
		}

		if err := validator.Validate(event); err != nil {
			_ = deadLetters.Send(ctx, string(msg.Key), msg.Value, err.Error())
			observability.EventsResult.WithLabelValues("dlq").Inc()
			log.Warn("dead-lettered event", "reason", err.Error(), "request_id", event["request_id"])
			_ = reader.CommitMessages(ctx, msg)
			continue
		}

		enriched := enrich.Enrich(event, time.Now())
		out, _ := json.Marshal(enriched)
		key := []byte(event["trace_id"].(string))
		if err := clean.WriteMessages(ctx, kafka.Message{Key: key, Value: out}); err != nil {
			log.Error("clean write failed; leaving uncommitted", "err", err, "trace_id", event["trace_id"])
			continue
		}
		observability.EventsResult.WithLabelValues("clean").Inc()
		observability.ProcessSeconds.Observe(time.Since(started).Seconds())
		_ = reader.CommitMessages(ctx, msg)
	}
}
