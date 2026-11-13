def create_item(item: dict[str, object]) -> dict[str, object]:
    # Actual service logic would run here.
    return {"item_id": 1, "status": "created"}


def get_item(item_id: int) -> dict[str, object]:
    # Actual service logic would run here.
    return {"item_id": item_id, "name": "example item"}


def update_item(item_id: int, item: dict[str, object]) -> dict[str, object]:
    # Actual service logic would run here.
    return {"item_id": item_id, "status": "updated"}


def delete_item(item_id: int) -> dict[str, object]:
    # Actual service logic would run here.
    return {"item_id": item_id, "status": "deleted"}
