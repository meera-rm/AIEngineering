from fastapi import FastAPI

from example_service import create_item, delete_item, get_item, update_item


# Run with: uvicorn example_http_wrapper:app --host 0.0.0.0 --port 8000
app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/items", status_code=201)
def create_item_endpoint(item: dict[str, object]) -> dict[str, object]:
    return create_item(item)


@app.get("/items/{item_id}")
def get_item_endpoint(item_id: int) -> dict[str, object]:
    return get_item(item_id)


@app.put("/items/{item_id}")
def update_item_endpoint(
    item_id: int, item: dict[str, object]
) -> dict[str, object]:
    return update_item(item_id, item)


@app.delete("/items/{item_id}")
def delete_item_endpoint(item_id: int) -> dict[str, object]:
    return delete_item(item_id)
