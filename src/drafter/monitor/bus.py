from dataclasses import dataclass, field
from typing import Callable, Optional, Dict
from drafter.monitor.telemetry import TelemetryEvent


@dataclass
class Subscription:
    """
    Represents a subscription to a topic on the bus.

    :ivar topic: The topic to which the subscription is made.
    :ivar handler: The handler function to be called when an event is published to the topic.
    :ivar filter: An optional filter function to filter events.
    :ivar once: Whether the subscription should be removed after the first event.
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

    :ivar subscribers: The list of subscribers to the bus.
    """

    maximum_queue_size: int = 500
    subscribers: list[Subscription] = field(default_factory=list)

    def publish(self, event: TelemetryEvent) -> None:
        """
        Publish an event to the bus.

        :param event: The telemetry event to publish.
        """
        for subscription in self.subscribers:
            if (
                subscription.topic.startswith(event.event_type)
                or subscription.topic == "*"
            ):
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

        :param topic: The topic to subscribe to.
        :param handler: The handler to call when an event is published to the topic.
        """
        subscription = Subscription(topic, handler, filter, once)
        self.subscribers.append(subscription)
        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        """
        Unsubscribe a handler from the bus.

        :param subscription: The subscription to remove.
        """
        if subscription in self.subscribers:
            self.subscribers.remove(subscription)


MAIN_EVENT_BUS = EventBus()


def get_main_event_bus() -> EventBus:
    """
    Get the main event bus.

    :return: The main event bus.
    """
    return MAIN_EVENT_BUS


def reset_main_event_bus() -> None:
    """
    Reset the main event bus.
    """
    global MAIN_EVENT_BUS
    MAIN_EVENT_BUS = EventBus()


def set_main_event_bus(bus: EventBus) -> None:
    """
    Set the main event bus.

    :param bus: The event bus to set as the main event bus.
    """
    global MAIN_EVENT_BUS
    MAIN_EVENT_BUS = bus
