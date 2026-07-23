"""
The event bus used for telemetry across the system.

Defines `Subscription` and `EventBus`. Publishers emit TelemetryRecords;
subscribers register a topic string (with "*" matching every record), an
optional filter, and a handler. A record is dispatched to a subscription
when its topic relates to the record's kind (see `EventBus.process_event`
for the exact comparison). While no subscribers exist, published records
are queued (up to a maximum) for later delivery via
`process_unprocessed_events`.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from drafter.data.telemetry import TelemetryRecord


@dataclass
class Subscription:
    """
    Represents a subscription to a kind of record on the bus.

    Attributes:
        topic: The record kind to which the subscription is made ("*" for all).
        handler: The handler function to be called when a record is published to the topic.
        filter: An optional filter function to filter records.
        once: Whether the subscription should be removed after the first record.
    """

    topic: str
    handler: Callable[[TelemetryRecord], None]
    filter: Callable | None = None
    once: bool = False


@dataclass
class EventBus:
    """
    Represents an event bus for communication between
    different parts of the system.

    Attributes:
        subscribers: The list of subscribers to the bus.
        unprocessed_events: The list of unprocessed events. When
            there are no subscribers, events are queued here.
        maximum_queue_size: The maximum size of the event queue.
    """

    maximum_queue_size: int = 500
    subscribers: list[Subscription] = field(default_factory=list)
    unprocessed_events: list[TelemetryRecord] = field(default_factory=list)

    def publish(self, event: TelemetryRecord) -> None:
        """
        Publish a record to the bus.

        Args:
            event: The telemetry record to publish.
        """
        if len(self.unprocessed_events) >= self.maximum_queue_size:
            self.unprocessed_events.pop(0)
        if not self.subscribers:
            self.unprocessed_events.append(event)
        else:
            for subscription in self.subscribers:
                self.process_event(event, subscription)

    def process_event(self, event: TelemetryRecord, subscription: Subscription) -> None:
        """
        Process a record for a given subscription.

        Args:
            event: The telemetry record to process.
            subscription: The subscription to process the record for.
        """
        if subscription.topic.startswith(event.kind) or subscription.topic == "*":
            if subscription.filter is None or subscription.filter(event):
                subscription.handler(event)
            if subscription.once:
                self.unsubscribe(subscription)

    def subscribe(
        self,
        topic: str,
        handler: Callable[[TelemetryRecord], None],
        filter: Callable | None = None,
        once: bool = False,
    ) -> Subscription:
        """
        Subscribe a handler to a topic.

        Args:
            topic: The topic to subscribe to.
            handler: The handler to call when an event is published to the topic.
            filter: An optional filter function to filter events.
            once: Whether to only handle one event.

        Returns:
            The subscription object.
        """
        subscription = Subscription(topic, handler, filter, once)
        self.subscribers.append(subscription)
        return subscription

    def process_unprocessed_events(self):
        """Deliver queued events to the current subscribers.

        Runs every queued event through every subscription (subject to the
        usual topic and filter checks). The queue is not cleared, so events
        remain available for subscribers added later.
        """
        for subscription in self.subscribers:
            for event in self.unprocessed_events:
                self.process_event(event, subscription)

    def unsubscribe(self, subscription: Subscription) -> None:
        """
        Unsubscribe a handler from the bus.

        Args:
            subscription: The subscription to remove.
        """
        if subscription in self.subscribers:
            self.subscribers.remove(subscription)
