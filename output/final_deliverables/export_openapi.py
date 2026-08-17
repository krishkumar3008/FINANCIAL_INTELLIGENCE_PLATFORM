import os
import sys

sys.path.insert(0, os.path.abspath("."))
import json

from src.api.main import app


def export_openapi_and_postman(
    openapi_path: str = "docs/openapi.json",
    postman_path: str = "docs/postman_collection.json",
):
    """
    Exports OpenAPI 3.0 specification JSON and a basic Postman collection JSON.
    """
    os.makedirs(os.path.dirname(openapi_path), exist_ok=True)

    # 1. OpenAPI Spec
    openapi_schema = app.openapi()
    with open(openapi_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"[OK] Exported OpenAPI spec to {openapi_path}")

    # 2. Postman Collection
    item_list = []
    paths = openapi_schema.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            item_list.append(
                {
                    "name": details.get("summary", f"{method.upper()} {path}"),
                    "request": {
                        "method": method.upper(),
                        "header": [],
                        "url": {
                            "raw": f"http://localhost:8000{path}",
                            "protocol": "http",
                            "host": ["localhost"],
                            "port": "8000",
                            "path": [p for p in path.split("/") if p],
                        },
                        "description": details.get("description", ""),
                    },
                }
            )

    postman_collection = {
        "info": {
            "name": "Nifty 100 Financial Intelligence API Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": "Postman collection generated from FastAPI OpenAPI specification.",
        },
        "item": item_list,
    }

    with open(postman_path, "w", encoding="utf-8") as f:
        json.dump(postman_collection, f, indent=2)
    print(f"[OK] Exported Postman collection to {postman_path}")


if __name__ == "__main__":
    export_openapi_and_postman()
