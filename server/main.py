# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from fastapi import FastAPI

app = FastAPI(title="LanguageLearn API", version="0.1.0")


@app.get("/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
