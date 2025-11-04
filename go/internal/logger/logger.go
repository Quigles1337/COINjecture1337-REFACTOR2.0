// Structured logging for COINjecture daemon
package logger

import (
	"os"

	"github.com/sirupsen/logrus"
)

// Fields type alias for structured logging
type Fields = logrus.Fields

// Logger wraps logrus for structured logging
type Logger struct {
	*logrus.Logger
}

// NewLogger creates a new logger with specified level
func NewLogger(level string) *Logger {
	log := logrus.New()
	log.SetOutput(os.Stdout)
	log.SetFormatter(&logrus.JSONFormatter{
		TimestampFormat: "2006-01-02T15:04:05.000Z07:00",
	})

	// Parse log level
	logLevel, err := logrus.ParseLevel(level)
	if err != nil {
		logLevel = logrus.InfoLevel
	}
	log.SetLevel(logLevel)

	return &Logger{log}
}

// WithError adds error field to log entry
func (l *Logger) WithError(err error) *logrus.Entry {
	return l.Logger.WithError(err)
}

// WithField adds a single field to log entry
func (l *Logger) WithField(key string, value interface{}) *logrus.Entry {
	return l.Logger.WithField(key, value)
}

// WithFields adds multiple fields to log entry
func (l *Logger) WithFields(fields Fields) *logrus.Entry {
	return l.Logger.WithFields(fields)
}
