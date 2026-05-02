"""Offline topic data hub for local trading research workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Callable


Clock = Callable[[], float]
Subscriber = Callable[["DataEvent"], None]


@dataclass(frozen=True)
class DataEvent:
    """A point-in-time payload published to a topic."""

    topic: str
    payload: Any
    created_at: float
    sequence: int
    expires_at: float | None = None
    producer: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, now: float) -> bool:
        return self.expires_at is not None and now >= self.expires_at


@dataclass(frozen=True)
class Subscription:
    """A callback registration for an exact topic or suffix wildcard pattern."""

    token: int
    pattern: str
    owner: str | None = None


@dataclass
class _SubscriptionEntry:
    subscription: Subscription
    callback: Subscriber


class DataHub:
    """Small in-memory topic hub for offline research components.

    Topics keep their latest live event. Subscribers can register for exact
    topics or suffix wildcard patterns such as ``market:*``.
    """

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or monotonic
        self._topics: dict[str, DataEvent] = {}
        self._subscriptions: dict[int, _SubscriptionEntry] = {}
        self._next_sequence = 1
        self._next_subscription_token = 1
        self._published = 0
        self._delivered = 0
        self._expired = 0

    def publish(
        self,
        topic: str,
        payload: Any,
        *,
        ttl: float | None = None,
        producer: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DataEvent:
        """Publish a payload and notify matching live subscribers."""

        self._validate_topic(topic)
        if ttl is not None and ttl < 0:
            raise ValueError("ttl must be non-negative")

        self._purge_expired()
        now = self._clock()
        event = DataEvent(
            topic=topic,
            payload=payload,
            created_at=now,
            sequence=self._next_sequence,
            expires_at=None if ttl is None else now + ttl,
            producer=producer,
            metadata=dict(metadata or {}),
        )
        self._next_sequence += 1
        self._published += 1

        if event.is_expired(now):
            self._expired += 1
            return event

        self._topics[topic] = event
        for entry in list(self._subscriptions.values()):
            if self._matches(entry.subscription.pattern, topic):
                entry.callback(event)
                self._delivered += 1
        return event

    def peek(self, topic: str) -> DataEvent | None:
        """Return the latest live event for a topic, if present."""

        self._validate_topic(topic)
        self._purge_expired()
        return self._topics.get(topic)

    def subscribe(
        self,
        pattern: str,
        callback: Subscriber,
        *,
        owner: str | None = None,
    ) -> Subscription:
        """Subscribe to an exact topic or suffix wildcard pattern."""

        self._validate_pattern(pattern)
        token = self._next_subscription_token
        self._next_subscription_token += 1
        subscription = Subscription(token=token, pattern=pattern, owner=owner)
        self._subscriptions[token] = _SubscriptionEntry(subscription, callback)
        return subscription

    def unsubscribe(
        self,
        token: int | None = None,
        *,
        owner: str | None = None,
    ) -> int:
        """Remove subscriptions by token or owner and return the count removed."""

        if token is None and owner is None:
            raise ValueError("unsubscribe requires token or owner")

        removed = 0
        for subscription_token, entry in list(self._subscriptions.items()):
            token_matches = token is not None and subscription_token == token
            owner_matches = owner is not None and entry.subscription.owner == owner
            if token_matches or owner_matches:
                del self._subscriptions[subscription_token]
                removed += 1
        return removed

    def topics(self) -> list[str]:
        """Return live topic names in deterministic order."""

        self._purge_expired()
        return sorted(self._topics)

    def subscriptions(self) -> list[Subscription]:
        """Return active subscription descriptors."""

        return [entry.subscription for entry in self._subscriptions.values()]

    def stats(self) -> dict[str, int]:
        """Return lightweight operational counters and current live counts."""

        self._purge_expired()
        return {
            "topics": len(self._topics),
            "subscriptions": len(self._subscriptions),
            "published": self._published,
            "delivered": self._delivered,
            "expired": self._expired,
        }

    def _purge_expired(self) -> None:
        now = self._clock()
        for topic, event in list(self._topics.items()):
            if event.is_expired(now):
                del self._topics[topic]
                self._expired += 1

    @staticmethod
    def _matches(pattern: str, topic: str) -> bool:
        if pattern.endswith("*"):
            return topic.startswith(pattern[:-1])
        return pattern == topic

    @staticmethod
    def _validate_topic(topic: str) -> None:
        if not topic:
            raise ValueError("topic must be non-empty")
        if "*" in topic:
            raise ValueError("topic cannot contain wildcard characters")

    @staticmethod
    def _validate_pattern(pattern: str) -> None:
        if not pattern:
            raise ValueError("pattern must be non-empty")
        if "*" in pattern[:-1]:
            raise ValueError("wildcard is only supported as a suffix")


__all__ = ["DataEvent", "DataHub", "Subscription"]
