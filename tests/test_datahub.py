from trading_lab.datahub import DataHub


class ManualClock:
    def __init__(self, now: float = 0.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_publish_and_peek_keep_latest_topic_snapshot() -> None:
    clock = ManualClock()
    hub = DataHub(clock=clock)

    event = hub.publish("market:AAPL", {"price": 101.25}, ttl=10, producer="fixture")

    assert event.topic == "market:AAPL"
    assert hub.peek("market:AAPL").payload == {"price": 101.25}
    assert hub.peek("market:AAPL").producer == "fixture"


def test_ttl_expiry_uses_injected_clock() -> None:
    clock = ManualClock()
    hub = DataHub(clock=clock)

    hub.publish("market:AAPL", {"price": 101.25}, ttl=5)
    clock.advance(4.9)
    assert hub.peek("market:AAPL").payload == {"price": 101.25}

    clock.advance(0.2)
    assert hub.peek("market:AAPL") is None
    assert hub.stats()["expired"] == 1


def test_subscription_receives_exact_and_suffix_wildcard_topics() -> None:
    hub = DataHub(clock=ManualClock())
    seen: list[tuple[str, object]] = []

    hub.subscribe("market:*", lambda event: seen.append((event.topic, event.payload)))
    hub.subscribe("signals:ready", lambda event: seen.append((event.topic, event.payload)))

    hub.publish("market:AAPL", {"price": 101.25})
    hub.publish("signals:ready", True)
    hub.publish("research:ignored", "not a subscribed topic")

    assert seen == [
        ("market:AAPL", {"price": 101.25}),
        ("signals:ready", True),
    ]


def test_owner_token_unsubscribes_matching_subscriptions_only() -> None:
    hub = DataHub(clock=ManualClock())
    owned: list[str] = []
    other: list[str] = []

    hub.subscribe("market:*", lambda event: owned.append(event.topic), owner="research-run-1")
    hub.subscribe("market:*", lambda event: other.append(event.topic), owner="research-run-2")

    assert hub.unsubscribe(owner="research-run-1") == 1
    hub.publish("market:MSFT", {"price": 201.0})

    assert owned == []
    assert other == ["market:MSFT"]


def test_stats_and_topics_report_live_state() -> None:
    clock = ManualClock()
    hub = DataHub(clock=clock)

    hub.publish("market:AAPL", {"price": 101.25}, ttl=1)
    hub.publish("signals:alpha", {"score": 0.7})
    hub.subscribe("market:*", lambda event: None, owner="dashboard")
    clock.advance(2)

    assert hub.topics() == ["signals:alpha"]
    assert hub.stats() == {
        "topics": 1,
        "subscriptions": 1,
        "published": 2,
        "delivered": 0,
        "expired": 1,
    }


def test_snapshot_returns_matching_current_topic_events_with_metadata() -> None:
    hub = DataHub(clock=ManualClock())

    hub.publish(
        "market:quote:MSFT",
        {"last": 401.5},
        producer="fixture",
        metadata={"delay_class": "simulated", "source": "fixture"},
    )
    hub.publish("provider:status:fixture", {"state": "ok"}, producer="fixture")

    snapshot = hub.snapshot("market:*")

    assert [event.topic for event in snapshot] == ["market:quote:MSFT"]
    assert snapshot[0].metadata == {"delay_class": "simulated", "source": "fixture"}
    assert snapshot[0].producer == "fixture"
