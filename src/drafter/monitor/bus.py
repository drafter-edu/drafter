from dataclasses import dataclass, field
from typing import Callable, Optional
from drafter.monitor.telemetry import TelemetryEvent


@dataclass
class Subscription:
    """
    Represents a subscription to a topic on the bus.

    Attributes:
        topic: The topic to which the subscription is made.
        handler: The handler function to be called when an event is published to the topic.
        filter: An optional filter function to filter events.
        once: Whether the subscription should be removed after the first event.
    """

    topic: str
    handler: Callable[[TelemetryEvent], None]
    filter: Optional[Callable] = None
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
    unprocessed_events: list[TelemetryEvent] = field(default_factory=list)

    def publish(self, event: TelemetryEvent) -> None:
        """
        Publish an event to the bus.

        Args:
            event: The telemetry event to publish.
        """
        if len(self.unprocessed_events) >= self.maximum_queue_size:
            self.unprocessed_events.pop(0)
        if not self.subscribers:
            self.unprocessed_events.append(event)
        else:
            for subscription in self.subscribers:
                self.process_event(event, subscription)

    def process_event(self, event: TelemetryEvent, subscription: Subscription) -> None:
        """
        Process an event for a given subscription.

        Args:
            event: The telemetry event to process.
            subscription: The subscription to process the event for.
        """
        if subscription.topic.startswith(event.event_type) or subscription.topic == "*":
            if subscription.filter is None or subscription.filter(event):
                subscription.handler(event)
            if subscription.once:
                self.unsubscribe(subscription)

    def subscribe(
        self,
        topic: str,
        handler: Callable[[TelemetryEvent], None],
        filter: Optional[Callable] = None,
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
