"""Centralized log message templates.

Runtime code imports log messages from this module instead of keeping random
message strings inside services, workers, and entrypoints.
"""

WORKER_STARTING_LOG = "worker_starting"
WORKER_STOPPED_LOG = "worker_stopped"
WORKER_STOP_REQUESTED_LOG = "worker_stop_requested"

WORKER_CYCLE_STARTED_LOG = "price_alert_worker_cycle_started"
WORKER_CYCLE_FINISHED_LOG = "price_alert_worker_cycle_finished"
WORKER_CYCLE_FAILED_LOG = "price_alert_worker_cycle_failed"

WORKER_NO_ACTIVE_ALERTS_LOG = "price_alert_worker_no_active_alerts"
WORKER_NO_PRICES_LOG = "price_alert_worker_no_prices"

ALERT_TRIGGERED_LOG_TEMPLATE = (
    "price_alert_triggered alert_id={alert_id} user_id={user_id} symbol={symbol}"
)

ALERT_NOTIFICATION_FAILED_LOG_TEMPLATE = (
    "price_alert_notification_failed alert_id={alert_id} user_id={user_id}"
)

WHALE_WORKER_CYCLE_STARTED_LOG = "whale_alert_worker_cycle_started"
WHALE_WORKER_CYCLE_FINISHED_LOG = "whale_alert_worker_cycle_finished"
WHALE_WORKER_CYCLE_FAILED_LOG = "whale_alert_worker_cycle_failed"
WHALE_WORKER_NO_EVENTS_LOG = "whale_alert_worker_no_events"

WHALE_EVENT_CREATED_LOG_TEMPLATE = (
    "whale_event_created event_id={event_id} symbol={symbol} amount_usd={amount_usd}"
)

WHALE_EVENT_DUPLICATE_LOG_TEMPLATE = (
    "whale_event_duplicate transaction_hash={transaction_hash}"
)

WHALE_NOTIFICATION_SENT_LOG_TEMPLATE = (
    "whale_notification_sent event_id={event_id} user_id={user_id}"
)

WHALE_NOTIFICATION_FAILED_LOG_TEMPLATE = (
    "whale_notification_failed event_id={event_id} user_id={user_id}"
)

BOT_STARTING_LOG = "bot_starting"
BOT_STOP_REQUESTED_LOG = "bot_stop_requested"
BOT_STOPPED_LOG = "bot_stopped"
