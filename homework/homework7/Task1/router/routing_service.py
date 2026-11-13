import math
from pathlib import Path

from ticket_router import TicketRouter


DEFAULT_MODEL_PATH = Path(__file__).parent / "ticket_router.joblib"   

DEPARTMENTS = [
    "Billing and Payments",
    "Customer Service",
    "General Inquiry",
    "Human Resources",
    "IT Support",
    "Product Support",
    "Returns and Exchanges",
    "Sales and Pre-Sales",
    "Service Outages and Maintenance",
    "Technical Support",
]

class InvalidRequestError(Exception):
    """The request breaks the request schema."""

class RoutingServiceError(Exception):
    """The classifier could not be set up, failed, or returned invalid output."""


class RoutingService:
    """A service that routes tickets to departments."""

    def __init__(self, model_path: str | Path | None = None):
       
        self.model_path = Path(model_path) if model_path is not None else DEFAULT_MODEL_PATH

        try:
            self.router = TicketRouter.load(self.model_path)
        except Exception as e:
            raise RoutingServiceError(f"Failed to load classifier from {self.model_path}") from e



    def _check_output(self, output: dict) -> None:

        """Raise RoutingServiceError unless output satisfies the response schema."""

        if not isinstance(output, dict):
            raise RoutingServiceError("Classifier output must be a dictionary.")
        
        if "recommended_department" not in output or "class_scores" not in output:
            raise RoutingServiceError("Classifier output is missing required keys.")

        recommended_department = output["recommended_department"]
        class_scores = output["class_scores"]

        # class_scores: a dict with exactly the 10 departments as keys
        if not isinstance(class_scores, dict):
            raise RoutingServiceError("class_scores must be a dictionary.")
        if len(class_scores) != len(DEPARTMENTS) or set(class_scores) != set(DEPARTMENTS):
            raise RoutingServiceError("class_scores must have exactly the allowed departments as keys.")

        # recommended_department: one of the allowed departments
        if not isinstance(recommended_department, str) or recommended_department not in DEPARTMENTS:
            raise RoutingServiceError("recommended_department is not an allowed department.")

        # every score: a finite float
        for score in class_scores.values():
            if not isinstance(score, float) or not math.isfinite(score):
                raise RoutingServiceError("class_scores values must be finite floats.")

        # tie rule: the recommendation must hold the top score (ties allowed)
        if class_scores[recommended_department] != max(class_scores.values()):
            raise RoutingServiceError("recommended_department does not have the top score.")



    def route_ticket(self, request: dict) -> dict:
        """Route a ticket to a department.

        Args:
            request: dict with a "body" string (at least one non-whitespace character).

        Returns:
            A dictionary with the recommended department and class scores.
             {"recommended_department": str, "class_scores": dict[str, float]}


        Raises:
            InvalidRequestError: the request breaks the request schema.
            RoutingServiceError: the classifier failed or returned invalid output.
        """

        if not isinstance(request, dict):
            raise InvalidRequestError("Request must be a dictionary.")

        ticket_body = request.get("body")

        if not isinstance(ticket_body, str) or not ticket_body.strip():
            raise InvalidRequestError("Ticket body must be a non-empty string.")

        try:
            output = self.router.predict(ticket_body)
        except Exception as e:
            raise RoutingServiceError("classifier failed while scoring the request") from e
            

        self._check_output(output)   
                       # raises RoutingServiceError if invalid
        return {
            "recommended_department": output["recommended_department"],
            "class_scores": output["class_scores"],
        }


