# Service Layer: Core Utilities & Authorization Strategy

This document outlines the proposed strategies for handling error handling, logging, dependency injection, and authorization within the backend service layer.

## 1. Error Handling Strategy

* **API-Facing Errors:** Use FastAPI's `HTTPException` within service functions for errors that need to be directly communicated to the API client with appropriate HTTP status codes (e.g., 404 Not Found, 403 Forbidden, 400 Bad Request, 409 Conflict, 422 Unprocessable Entity). This is already partially implemented in several service functions.
* **Business Logic Errors:** (Optional Enhancement) Define custom Python exception classes (e.g., `InsufficientFundsError`, `LastAdminError`, `InvalidUnitValueError`) for specific, potentially recoverable business rule violations within services. These can be caught within the service or allowed to propagate up to the API layer.
* **Database/Unexpected Errors:** Use standard Python `try...except` blocks to catch expected database exceptions (e.g., `sqlalchemy.exc.IntegrityError` for unique constraint violations) and other unexpected errors (`Exception`). Log these errors thoroughly.
* **Centralized Handling (FastAPI):** Leverage FastAPI's exception handlers (using `@app.exception_handler(...)` in `main.py`) to catch custom business logic exceptions or unhandled errors. This allows for centralized logging and consistent formatting of error responses returned to the client. For instance, an unhandled `Exception` could be caught, logged, and returned as a generic 500 Internal Server Error response.

## 2. Logging Strategy

* **Module:** Use Python's built-in `logging` module.
* **Configuration:** Configure a root logger in `main.py` or a dedicated logging configuration file (`logging.conf`). Set:
    * **Level:** Control verbosity (e.g., `logging.INFO` for production, `logging.DEBUG` for development).
    * **Format:** Define a consistent log format including timestamp, level, module name, line number, and message (e.g., `%(asctime)s %(levelname)-8s %(name)s:%(lineno)d - %(message)s`).
    * **Handlers:** Direct logs to appropriate outputs (e.g., `logging.StreamHandler` for console output, `logging.FileHandler` or `logging.handlers.RotatingFileHandler` for file output).
* **Usage:**
    * In each service module (`*.py` file), get a logger instance: `log = logging.getLogger(__name__)`.
    * Log key events:
        * `log.debug()`: Detailed information, function entry/exit, variable values useful for debugging.
        * `log.info()`: Confirmation of successful operations, significant state changes (e.g., "User X created Club Y").
        * `log.warning()`: Potential issues or non-critical errors (e.g., "Market data for asset Z not found, excluding from NAV").
        * `log.error()`: Errors that prevent an operation from completing but might be recoverable or expected (e.g., validation errors caught in `try...except`).
        * `log.exception()`: Used within `except` blocks to log errors along with the stack trace for unexpected failures.
    * Include relevant context in log messages (e.g., Club IDs, User IDs, Asset Symbols).

## 3. Dependency Injection (DI) Strategy

* **Framework:** Utilize FastAPI's built-in dependency injection system (`Depends`).
* **Database Session:**
    * Create a dependency function (e.g., in `backend/api/dependencies.py`) that manages the lifecycle of an `AsyncSession`. This function should:
        * Create a session using the `async_sessionmaker`.
        * `yield` the session to the route function/dependent.
        * Wrap the `yield` in a `try...finally` block to ensure `session.close()` is called.
        * Wrap the `yield` in a `try...except` block to handle exceptions during the request, perform a `session.rollback()`, and re-raise the exception. The final `session.commit()` should happen *only if no exceptions occurred*, typically just before the `finally` block.
    * Inject this dependency into API route functions: `db: AsyncSession = Depends(get_db_session)`.
    * Pass the obtained `db` session down into the service layer functions as needed.
* **Service Dependencies:**
    * For the current structure where services are collections of functions, direct function calls between services (e.g., `accounting_service` calling `crud_member_tx.get_member_unit_balance`) are acceptable.
    * (Future Option) If services become more complex or stateful, consider structuring them as classes and injecting instances using `Depends`.

## 4. Authorization Strategy

* **Authentication:** Assume Auth0 integration (likely via middleware or a security dependency in FastAPI) provides the authenticated user's `auth0_sub` and potentially other token claims.
* **User Mapping:** Use the existing `user_service.get_or_create_user_by_auth0` function, likely called within an authentication dependency, to get the internal `User` object corresponding to the `auth0_sub`. This internal `User` object represents the "current user".
* **Role-Based Access Control (RBAC):**
    * **Permission Checks:** Implement checks within service functions that require specific permissions (e.g., adding members, deleting clubs).
    * **Mechanism:**
        1.  Pass the `requesting_user: User` object (obtained via the authentication dependency) to the service function.
        2.  Fetch the `ClubMembership` for the `requesting_user` and the relevant `club_id` using `crud_membership.get_club_membership_by_user_and_club`.
        3.  Check the `role` attribute on the membership against the required role (e.g., `if membership.role != ClubRole.ADMIN:`).
        4.  Raise `HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")` if the check fails. (This is partially implemented in `add_club_member`, `update_member_role`, `remove_club_member`).
* **Refinement (Dependencies):** Create reusable FastAPI dependency functions to encapsulate common authorization checks:
    * `get_current_active_user(...)`: A dependency that verifies the Auth0 token, fetches/creates the internal user using `get_or_create_user_by_auth0`, checks if the user `is_active`, and returns the `User` object.
    * `require_club_admin(club_id: uuid.UUID, current_user: User = Depends(get_current_active_user))`: A dependency that takes the `club_id` (e.g., from path parameters) and the `current_user`, fetches their membership for that club, and raises HTTP 403 if they are not an ADMIN.
    * Inject these dependencies into API routes that require specific permissions, simplifying the route function and service layer signatures.

