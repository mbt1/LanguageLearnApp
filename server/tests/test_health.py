# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
