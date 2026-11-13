from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from routing_service import InvalidRequestError, RoutingService, RoutingServiceError

service: RoutingService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the classifier once at startup; reused for every request.
    global service
    service = RoutingService()
    yield


app = FastAPI(title="Ticket routing service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/route")
def route(request: dict) -> dict:
    try:
        return service.route_ticket(request)
    except InvalidRequestError as exc:
        raise HTTPException(422, str(exc)) from exc
    except RoutingServiceError as exc:
        raise HTTPException(500, str(exc)) from exc
