# Architectural Decisions

This document captures key architectural decisions made in building the Loan Underwriting & Lender Matching System.

## ADR-001: Extensible Criteria Evaluator Pattern

### Context
The system needs to evaluate loan applications against many different types of criteria (FICO scores, business age, equipment types, geography, etc.). These criteria types will evolve over time as new lenders are added.

### Decision
Implement a method-based evaluator pattern where each criteria type maps to a specific `_evaluate_{type}` method in the MatchingEngine class.

### Rationale
- **Extensibility**: Adding a new criteria type only requires adding one new method
- **Isolation**: Each evaluator is independent and testable
- **Type Safety**: Criteria types are validated against known types
- **Fallback**: Unknown criteria types are handled gracefully with a default pass

### Implementation
```python
def _evaluate_criteria(self, criteria, application):
    evaluator_method = getattr(
        self, 
        f"_evaluate_{criteria.criteria_type}", 
        self._evaluate_unknown
    )
    return evaluator_method(criteria, application)
```

### Alternatives Considered
1. **Strategy Pattern with Classes**: More complex, requires registration
2. **Configuration-Driven Rules**: Less flexible for complex logic
3. **Expression Language**: Higher learning curve, security concerns

---

## ADR-002: PostgreSQL over MySQL

### Context
Using PostgreSQL as per instructions for kaaj assignment. This system needs to store complex JSON structures (criteria configurations) and support advanced querying.

### Decision
Use PostgreSQL with JSONB support for storing flexible criteria configurations.

### Rationale
- **JSONB Support**: Native JSON querying and indexing
- **Better Concurrency**: MVCC handles concurrent reads better
- **Advanced Features**: CTEs, window functions for analytics
- **Async Drivers**: asyncpg provides excellent async performance

### Trade-offs
- Team may need to adapt to PostgreSQL-specific syntax
- Different tooling from MySQL ecosystem

---

## ADR-003: Hatchet for Workflow Orchestration

### Context
Underwriting workflows involve multiple steps that may need retry logic, observability, and coordination.

### Decision
Use Hatchet SDK for workflow orchestration instead of Celery or custom queues.

### Rationale
- **Built-in Retries**: Configurable retry policies per step
- **Observability**: Dashboard for monitoring workflow runs
- **Step Dependencies**: Natural DAG representation
- **Concurrency Control**: Built-in rate limiting and concurrency limits

### Trade-offs
- External dependency on Hatchet service
- Learning curve for team
- Cost considerations for high-volume usage

---

## ADR-004: Normalized Database Schema

### Context
Lenders have multiple programs, each with multiple criteria. Need to decide between normalized schema vs. JSON blob storage.

### Decision
Fully normalized schema with separate tables for Lenders, Programs, and Criteria.

### Rationale
- **Query Flexibility**: Easy to find all criteria of a specific type
- **Referential Integrity**: Foreign keys ensure data consistency
- **Indexing**: Can index specific criteria fields for performance
- **Migrations**: Schema changes are explicit and versioned

### Trade-offs
- More complex queries to load full lender configuration
- Multiple joins required for complete picture
- API needs to handle nested object creation/updates

---

## ADR-005: Match Score Calculation

### Context
Need to rank lenders by how well an application matches their criteria, not just pass/fail.

### Decision
Calculate weighted scores based on criteria weights and pass rates.

### Formula
```
match_score = (Σ passed_weight × weight) / (Σ all_weight) × 100
```

### Rationale
- **Differentiation**: Distinguishes between barely qualifying and strongly qualifying
- **Weights**: Lenders can mark certain criteria as more important
- **Transparency**: Score breakdown shows which criteria drove the result

### Future Enhancements
- Tiered scoring (e.g., FICO > 720 gets bonus points)
- Machine learning-based scoring
- Historical approval rate correlation

---

## ADR-006: API Design - Nested vs. Flat

### Context
How should the API handle related resources (Lender → Programs → Criteria)?

### Decision
Hybrid approach:
- GET requests return nested structures
- POST/PUT for child resources use explicit parent paths

### Examples
```
GET  /lenders/{id}                           → Returns lender with nested programs/criteria
POST /lenders/{id}/programs                  → Creates program under lender
POST /lenders/{id}/programs/{pid}/criteria   → Creates criteria under program
```

### Rationale
- **Read Efficiency**: Single request gets full picture
- **Write Clarity**: Explicit parent IDs prevent ambiguity
- **REST Conventions**: Follows standard resource nesting patterns

---

## ADR-007: Frontend State Management

### Context
Need to manage server state (lenders, applications) and form state efficiently.

### Decision
Use React Query for server state + React Hook Form for form state.

### Rationale
- **React Query**: Handles caching, background refetching, optimistic updates
- **No Redux**: Avoids boilerplate for simple server-state sync
- **React Hook Form**: Minimal re-renders, built-in validation

### Trade-offs
- Less centralized state compared to Redux
- Query invalidation requires careful coordination

---

## ADR-008: Criteria Value Storage

### Context
Different criteria types need different value formats (numbers, lists, ranges).

### Decision
Single criteria table with multiple nullable value columns:
- `numeric_value`: Single number (e.g., min FICO)
- `numeric_value_min`, `numeric_value_max`: Range values
- `string_value`: Single string
- `list_values`: JSON array for lists (states, industries)

### Rationale
- **Single Table**: Simpler queries, no type discrimination
- **Explicit Columns**: Type-safe, indexable
- **Nullable**: Only populate relevant columns per criteria type

### Alternatives Considered
1. **Separate Tables per Type**: More normalized but complex joins
2. **Single JSON Column**: Flexible but harder to query/index
3. **EAV Pattern**: Too complex, poor query performance

---

## ADR-009: Error Handling Strategy

### Context
How should the system handle and communicate errors?

### Decision
Layered error handling:
1. **Validation Errors**: 422 with field-level details
2. **Business Logic Errors**: 400 with descriptive messages
3. **Not Found**: 404 with resource type
4. **Server Errors**: 500 with correlation ID

### Implementation
```python
class UnderwritingError(Exception):
    def __init__(self, message: str, code: str, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
```

### Rationale
- **Consistency**: All errors follow same structure
- **Actionability**: Errors include enough detail to fix issues
- **Observability**: Correlation IDs enable log tracing

---

## ADR-010: Logging and Observability

### Context
Need visibility into system behavior, especially during underwriting runs.

### Decision
Structured JSON logging with contextual fields:
- Request ID propagation
- Workflow run correlation
- Application and lender context in evaluations

### Implementation
```python
logger.info(
    "Criteria evaluated",
    extra={
        "request_id": request_id,
        "application_id": app.id,
        "lender_id": lender.id,
        "criteria_type": criteria.criteria_type,
        "passed": passed
    }
)
```

### Rationale
- **Searchability**: JSON logs easily searched in log aggregators
- **Context**: Always know which application/lender caused an event
- **Performance**: Async logging doesn't block requests
