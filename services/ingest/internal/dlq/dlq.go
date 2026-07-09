// Package dlq publishes poison messages to the dead-letter topic, attaching the
// validation reason so they can be triaged without re-running the validator.
package dlq

import (
	"context"
	"encoding/json"

	"github.com/segmentio/kafka-go"
)

type Writer struct {
	w *kafka.Writer
}

func New(brokers []string, topic string) *Writer {
	return &Writer{w: &kafka.Writer{
		Addr:     kafka.TCP(brokers...),
		Topic:    topic,
		Balancer: &kafka.Hash{},
	}}
}

// Record is the envelope written to the DLQ: the original bytes plus why it
// failed. Keeping the raw payload means nothing is lost.
type Record struct {
	Reason  string          `json:"validation_error"`
	Payload json.RawMessage `json:"payload"`
}

func (d *Writer) Send(ctx context.Context, key string, raw []byte, reason string) error {
	rec := Record{Reason: reason, Payload: raw}
	body, err := json.Marshal(rec)
	if err != nil {
		return err
	}
	return d.w.WriteMessages(ctx, kafka.Message{Key: []byte(key), Value: body})
}

func (d *Writer) Close() error { return d.w.Close() }
