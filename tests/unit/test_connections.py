"""
Tests for connection implementations (Strategy pattern targets).

Each connection is tested with mocked external dependencies so the test
suite can run without Kafka, Redis, or a live HTTP endpoint.
"""

import io
import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.fraud_generator.connections.stdout_connection import StdoutConnection
from src.fraud_generator.connections.kafka_connection import KafkaConnection
from src.fraud_generator.connections.webhook_connection import WebhookConnection
from src.fraud_generator.connections.redis_stream_connection import RedisStreamConnection

_HAS_KAFKA = KafkaConnection.is_available()


# ── StdoutConnection ─────────────────────────────────────────────────────────

class TestStdoutConnection:
    def test_is_available(self):
        assert StdoutConnection.is_available() is True

    def test_name(self):
        conn = StdoutConnection()
        assert conn.name == "Standard Output"

    def test_send_before_connect_raises(self):
        conn = StdoutConnection()
        with pytest.raises(RuntimeError, match="Not connected"):
            conn.send({"key": "value"})

    def test_send_writes_json_to_output(self):
        buf = io.StringIO()
        conn = StdoutConnection()
        conn.connect(output=buf)
        result = conn.send({"transaction_id": "tx_001", "valor": 99.90})
        assert result is True
        output = buf.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["transaction_id"] == "tx_001"
        assert parsed["valor"] == 99.90

    def test_send_pretty_prints(self):
        buf = io.StringIO()
        conn = StdoutConnection()
        conn.connect(pretty=True, output=buf)
        conn.send({"a": 1})
        output = buf.getvalue()
        assert "\n" in output  # pretty-printed JSON has newlines

    def test_count_increments(self):
        buf = io.StringIO()
        conn = StdoutConnection()
        conn.connect(output=buf)
        conn.send({"x": 1})
        conn.send({"x": 2})
        assert conn.count == 2

    def test_close_resets_connected(self):
        conn = StdoutConnection()
        conn.connect()
        assert conn._connected is True
        conn.close()
        assert conn._connected is False

    def test_context_manager(self):
        buf = io.StringIO()
        with StdoutConnection() as conn:
            conn.connect(output=buf)
            conn.send({"z": 42})
        assert conn._connected is False

    def test_send_batch(self):
        buf = io.StringIO()
        conn = StdoutConnection()
        conn.connect(output=buf)
        count = conn.send_batch([{"i": 1}, {"i": 2}, {"i": 3}])
        assert count == 3
        assert conn.count == 3


# ── KafkaConnection ──────────────────────────────────────────────────────────

class TestKafkaConnection:
    def test_name(self):
        conn = KafkaConnection()
        assert conn.name == "Apache Kafka"

    def test_send_before_connect_raises(self):
        conn = KafkaConnection()
        with pytest.raises(RuntimeError, match="Not connected"):
            conn.send({"key": "value"})

    @patch("src.fraud_generator.connections.kafka_connection.KafkaConnection.is_available", return_value=True)
    def test_connect_creates_producer(self, _mock_avail):
        mock_producer = MagicMock()
        mock_kafka_module = MagicMock()
        mock_kafka_module.KafkaProducer.return_value = mock_producer

        with patch.dict("sys.modules", {"kafka": mock_kafka_module}):
            conn = KafkaConnection()
            conn.connect(bootstrap_servers="localhost:9092", topic="test-topic")
            assert conn._connected is True
            assert conn.default_topic == "test-topic"

    @patch("src.fraud_generator.connections.kafka_connection.KafkaConnection.is_available", return_value=True)
    def test_send_calls_producer(self, _mock_avail):
        mock_future = MagicMock()
        mock_future.get.return_value = None
        mock_producer = MagicMock()
        mock_producer.send.return_value = mock_future
        mock_kafka_module = MagicMock()
        mock_kafka_module.KafkaProducer.return_value = mock_producer

        with patch.dict("sys.modules", {"kafka": mock_kafka_module}):
            conn = KafkaConnection()
            conn.connect(topic="txns")
            result = conn.send({"id": "tx_1"}, key="k1")

        assert result is True
        mock_producer.send.assert_called_once_with("txns", value={"id": "tx_1"}, key="k1")

    @patch("src.fraud_generator.connections.kafka_connection.KafkaConnection.is_available", return_value=True)
    def test_send_returns_false_on_error(self, _mock_avail):
        mock_future = MagicMock()
        mock_future.get.side_effect = Exception("Broker unavailable")
        mock_producer = MagicMock()
        mock_producer.send.return_value = mock_future
        mock_kafka_module = MagicMock()
        mock_kafka_module.KafkaProducer.return_value = mock_producer

        with patch.dict("sys.modules", {"kafka": mock_kafka_module}):
            conn = KafkaConnection()
            conn.connect(topic="txns")
            result = conn.send({"id": "tx_fail"})

        assert result is False

    @patch("src.fraud_generator.connections.kafka_connection.KafkaConnection.is_available", return_value=True)
    def test_close_flushes_and_closes(self, _mock_avail):
        mock_producer = MagicMock()
        mock_kafka_module = MagicMock()
        mock_kafka_module.KafkaProducer.return_value = mock_producer

        with patch.dict("sys.modules", {"kafka": mock_kafka_module}):
            conn = KafkaConnection()
            conn.connect(topic="txns")
            conn.close()

        mock_producer.flush.assert_called_once()
        mock_producer.close.assert_called_once()
        assert conn._connected is False

    def test_is_available_without_kafka(self):
        with patch.dict("sys.modules", {"kafka": None}):
            assert KafkaConnection.is_available() is False


# ── WebhookConnection ────────────────────────────────────────────────────────

class TestWebhookConnection:
    def test_name(self):
        conn = WebhookConnection()
        assert conn.name == "HTTP Webhook"

    def test_send_before_connect_raises(self):
        conn = WebhookConnection()
        with pytest.raises(RuntimeError, match="Not connected"):
            conn.send({"key": "value"})

    @patch("src.fraud_generator.connections.webhook_connection.WebhookConnection.is_available", return_value=True)
    def test_connect_creates_session(self, _mock_avail):
        with patch("requests.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            conn = WebhookConnection()
            conn.connect(url="https://example.com/webhook")

            assert conn._connected is True
            assert conn.url == "https://example.com/webhook"
            assert conn.method == "POST"

    @patch("src.fraud_generator.connections.webhook_connection.WebhookConnection.is_available", return_value=True)
    def test_send_returns_true_on_200(self, _mock_avail):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response

        with patch("requests.Session", return_value=mock_session):
            conn = WebhookConnection()
            conn.connect(url="https://example.com/hook")
            result = conn.send({"data": "test"})

        assert result is True
        mock_session.request.assert_called_once()

    @patch("src.fraud_generator.connections.webhook_connection.WebhookConnection.is_available", return_value=True)
    def test_send_returns_false_on_500(self, _mock_avail):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response

        with patch("requests.Session", return_value=mock_session):
            conn = WebhookConnection()
            conn.connect(url="https://example.com/hook")
            result = conn.send({"data": "err"})

        assert result is False

    @patch("src.fraud_generator.connections.webhook_connection.WebhookConnection.is_available", return_value=True)
    def test_send_returns_false_on_exception(self, _mock_avail):
        mock_session = MagicMock()
        mock_session.request.side_effect = ConnectionError("timeout")

        with patch("requests.Session", return_value=mock_session):
            conn = WebhookConnection()
            conn.connect(url="https://example.com/hook")
            result = conn.send({"data": "timeout"})

        assert result is False

    @patch("src.fraud_generator.connections.webhook_connection.WebhookConnection.is_available", return_value=True)
    def test_close_shuts_down_session_and_executor(self, _mock_avail):
        mock_session = MagicMock()

        with patch("requests.Session", return_value=mock_session):
            conn = WebhookConnection()
            conn.connect(url="https://example.com/hook")
            conn.close()

        mock_session.close.assert_called_once()
        assert conn._connected is False


# ── RedisStreamConnection ────────────────────────────────────────────────────

class TestRedisStreamConnection:
    def test_name(self):
        conn = RedisStreamConnection()
        assert conn.name == "Redis Stream"

    def test_send_before_connect_returns_false(self):
        conn = RedisStreamConnection()
        assert conn.send({"x": 1}) is False

    @patch("src.fraud_generator.connections.redis_stream_connection.RedisStreamConnection.is_available", return_value=True)
    def test_connect_sets_keys(self, _mock_avail):
        mock_client = MagicMock()

        with patch("redis.Redis") as mock_redis_cls:
            mock_redis_cls.from_url.return_value = mock_client

            conn = RedisStreamConnection()
            conn.connect(redis_url="redis://localhost:6379/0", stream_id="test_stream")

            assert conn._connected is True
            assert conn._stream_key == "stream:test_stream"
            assert conn._count_key == "stream:test_stream:count"
            assert conn._status_key == "stream:test_stream:status"
            mock_client.set.assert_called_once_with("stream:test_stream:status", "running", ex=86400)

    @patch("src.fraud_generator.connections.redis_stream_connection.RedisStreamConnection.is_available", return_value=True)
    def test_send_buffers_until_batch_size(self, _mock_avail):
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_client.pipeline.return_value = mock_pipe

        with patch("redis.Redis") as mock_redis_cls:
            mock_redis_cls.from_url.return_value = mock_client

            conn = RedisStreamConnection()
            conn.connect(stream_id="s1", batch_size=3)

            conn.send({"i": 1})
            conn.send({"i": 2})
            mock_client.pipeline.assert_not_called()

            conn.send({"i": 3})
            mock_client.pipeline.assert_called_once()
            assert mock_pipe.xadd.call_count == 3

    @patch("src.fraud_generator.connections.redis_stream_connection.RedisStreamConnection.is_available", return_value=True)
    def test_should_stop_reads_status_key(self, _mock_avail):
        mock_client = MagicMock()
        mock_client.get.return_value = "stop"

        with patch("redis.Redis") as mock_redis_cls:
            mock_redis_cls.from_url.return_value = mock_client
            conn = RedisStreamConnection()
            conn.connect(stream_id="s2")
            assert conn.should_stop() is True

        mock_client.get.return_value = "running"
        with patch("redis.Redis") as mock_redis_cls:
            mock_redis_cls.from_url.return_value = mock_client
            conn2 = RedisStreamConnection()
            conn2.connect(stream_id="s3")
            assert conn2.should_stop() is False

    @patch("src.fraud_generator.connections.redis_stream_connection.RedisStreamConnection.is_available", return_value=True)
    def test_close_sets_completed_status(self, _mock_avail):
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_client.pipeline.return_value = mock_pipe

        with patch("redis.Redis") as mock_redis_cls:
            mock_redis_cls.from_url.return_value = mock_client
            conn = RedisStreamConnection()
            conn.connect(stream_id="s4")
            conn.close()

        mock_client.set.assert_any_call("stream:s4:status", "completed", ex=3600)
        mock_client.close.assert_called_once()
        assert conn._connected is False
