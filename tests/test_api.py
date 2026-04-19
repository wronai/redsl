from fastapi.testclient import TestClient

from redsl import __version__
from redsl.api import create_app


def test_create_app_registers_single_health_route():
    app = create_app()
    health_routes = [route for route in app.routes if getattr(route, "path", None) == "/health"]

    assert len(health_routes) == 1


def test_health_endpoint_returns_expected_payload():
    client = TestClient(create_app())

    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["agent"] == "conscious-refactor"
    assert payload["version"] == __version__
    assert "memory" in payload


def test_examples_list_endpoint():
    client = TestClient(create_app())
    response = client.get("/examples")
    assert response.status_code == 200
    payload = response.json()
    assert "examples" in payload
    names = [e["name"] for e in payload["examples"]]
    assert "basic_analysis" in names
    assert "memory_learning" in names
    assert "awareness" in names
    assert "pyqual" in names
    assert "audit" in names
    assert "pr_bot" in names
    assert "badge" in names
    assert all(e["has_advanced"] for e in payload["examples"])


def test_examples_run_endpoint():
    client = TestClient(create_app())
    response = client.post("/examples/run", json={"name": "memory_learning", "scenario": "default"})
    assert response.status_code == 200
    payload = response.json()
    assert "output" in payload
    assert "EPISODIC" in payload["output"]


def test_examples_yaml_endpoint():
    client = TestClient(create_app())
    response = client.get("/examples/memory_learning/yaml?scenario=default")
    assert response.status_code == 200
    payload = response.json()
    assert "title" in payload
    assert "memory" in payload


def test_examples_run_unknown_returns_error():
    client = TestClient(create_app())
    response = client.post("/examples/run", json={"name": "nonexistent"})
    assert response.status_code == 200
    payload = response.json()
    assert "error" in payload


def test_debug_config_masks_sensitive_environment_values(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    monkeypatch.setenv("REFACTOR_DRY_RUN", "true")
    client = TestClient(create_app())

    response = client.get("/debug/config?show_env=true")
    assert response.status_code == 200
    payload = response.json()

    assert payload["env_vars"]["OPENROUTER_API_KEY"] == "<redacted>"
    assert payload["env_vars"]["REFACTOR_DRY_RUN"] == "true"
