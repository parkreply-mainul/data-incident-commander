"""Immutable human-controlled incident workflow."""

from __future__ import annotations

from datetime import datetime

from pydantic import model_validator

from .base import StrictModel, utc_datetime
from .models import IncidentState, StateTransition


class InvalidStateTransition(ValueError):
    """Raised when a requested workflow transition is not authorized."""


_VALID_TRANSITIONS: dict[IncidentState, frozenset[IncidentState]] = {
    IncidentState.DRAFT: frozenset({IncidentState.INVESTIGATED, IncidentState.FAILED}),
    IncidentState.INVESTIGATED: frozenset({IncidentState.AWAITING_APPROVAL, IncidentState.FAILED}),
    IncidentState.AWAITING_APPROVAL: frozenset({IncidentState.APPROVED, IncidentState.FAILED}),
    IncidentState.APPROVED: frozenset({IncidentState.WRITEBACK_PENDING, IncidentState.FAILED}),
    IncidentState.WRITEBACK_PENDING: frozenset(
        {IncidentState.RECORDED, IncidentState.FAILED}
    ),
    IncidentState.RECORDED: frozenset({IncidentState.RESOLVED, IncidentState.FAILED}),
    IncidentState.RESOLVED: frozenset(),
    IncidentState.FAILED: frozenset(),
}

_POST_APPROVAL_STATES = frozenset(
    {
        IncidentState.APPROVED,
        IncidentState.WRITEBACK_PENDING,
        IncidentState.RECORDED,
    }
)


class ApprovalStateMachine(StrictModel):
    current_state: IncidentState = IncidentState.DRAFT
    history: tuple[StateTransition, ...] = ()

    @staticmethod
    def _failure_origin(history: tuple[StateTransition, ...]) -> IncidentState | None:
        if not history or history[-1].to_state is not IncidentState.FAILED:
            return None
        return history[-1].from_state

    @model_validator(mode="after")
    def validates_restored_history(self) -> "ApprovalStateMachine":
        expected_state = IncidentState.DRAFT
        previous_time: datetime | None = None
        failed_from_state: IncidentState | None = None
        for transition in self.history:
            if transition.from_state is not expected_state:
                raise ValueError("transition history is not contiguous from DRAFT")
            is_post_approval_retry = failed_from_state in _POST_APPROVAL_STATES
            confirmations_are_valid = (
                transition.approval_remains_valid
                and transition.payload_binding_unchanged
                if is_post_approval_retry
                else not transition.approval_remains_valid
                and not transition.payload_binding_unchanged
            )
            is_valid_retry = (
                expected_state is IncidentState.FAILED
                and failed_from_state is not None
                and transition.to_state is failed_from_state
                and transition.retry_action
                and confirmations_are_valid
            )
            if (
                transition.to_state not in _VALID_TRANSITIONS[expected_state]
                and not is_valid_retry
            ):
                raise ValueError(
                    f"transition history contains invalid step "
                    f"{expected_state.value} -> {transition.to_state.value}"
                )
            if (
                transition.to_state is IncidentState.APPROVED
                and not is_valid_retry
                and not transition.approval_reason
            ):
                raise ValueError("restored approval transition requires approval_reason")
            if transition.to_state is IncidentState.FAILED and not transition.failure_reason:
                raise ValueError("restored failure transition requires failure_reason")
            if expected_state is not IncidentState.FAILED and transition.retry_action:
                raise ValueError("retry_action is valid only when restoring from FAILED")
            if (
                transition.approval_remains_valid
                or transition.payload_binding_unchanged
            ) and not (
                expected_state is IncidentState.FAILED
                and failed_from_state in _POST_APPROVAL_STATES
                and transition.retry_action
                and transition.approval_remains_valid
                and transition.payload_binding_unchanged
            ):
                raise ValueError(
                    "approval and payload confirmations are valid only for "
                    "post-approval retry"
                )
            if previous_time is not None and transition.occurred_at < previous_time:
                raise ValueError("transition history timestamps must be monotonic")
            if transition.to_state is IncidentState.FAILED:
                failed_from_state = transition.from_state
            elif expected_state is IncidentState.FAILED:
                failed_from_state = None
            expected_state = transition.to_state
            previous_time = transition.occurred_at
        if self.current_state is not expected_state:
            raise ValueError("current_state does not agree with transition history")
        return self

    @property
    def failed_from_state(self) -> IncidentState | None:
        return self._failure_origin(self.history)

    @property
    def failure_reason(self) -> str | None:
        return self.history[-1].failure_reason if self.failed_from_state is not None else None

    @property
    def failed_at(self) -> datetime | None:
        return self.history[-1].occurred_at if self.failed_from_state is not None else None

    @property
    def failure_actor(self) -> str | None:
        return self.history[-1].actor if self.failed_from_state is not None else None

    def transition(
        self,
        to_state: IncidentState,
        *,
        actor: str,
        occurred_at: datetime,
        approval_reason: str | None = None,
        failure_reason: str | None = None,
    ) -> "ApprovalStateMachine":
        if to_state not in _VALID_TRANSITIONS[self.current_state]:
            raise InvalidStateTransition(f"{self.current_state.value} -> {to_state.value} is invalid")
        if to_state is IncidentState.APPROVED and not approval_reason:
            raise InvalidStateTransition("approval_reason is required for approval")
        if to_state is IncidentState.FAILED and not failure_reason:
            raise InvalidStateTransition("failure_reason is required when entering FAILED")
        transition = StateTransition(
            from_state=self.current_state,
            to_state=to_state,
            actor=actor,
            occurred_at=occurred_at,
            approval_reason=approval_reason,
            failure_reason=failure_reason,
        )
        if self.history and transition.occurred_at < self.history[-1].occurred_at:
            raise InvalidStateTransition("transition timestamps must be monotonic")
        return ApprovalStateMachine(
            current_state=to_state,
            history=self.history + (transition,),
        )

    def retry(
        self,
        *,
        actor: str,
        occurred_at: datetime,
        approval_remains_valid: bool = False,
        payload_binding_unchanged: bool = False,
    ) -> "ApprovalStateMachine":
        failed_from_state = self.failed_from_state
        if self.current_state is not IncidentState.FAILED or failed_from_state is None:
            raise InvalidStateTransition("retry requires a FAILED state with failure context")
        if failed_from_state in _POST_APPROVAL_STATES and not (
            approval_remains_valid and payload_binding_unchanged
        ):
            raise InvalidStateTransition(
                "post-approval retry requires valid approval and unchanged payload binding"
            )
        if failed_from_state not in _POST_APPROVAL_STATES and (
            approval_remains_valid or payload_binding_unchanged
        ):
            raise InvalidStateTransition(
                "approval and payload confirmations are valid only for post-approval retry"
            )
        retry_transition = StateTransition(
            from_state=IncidentState.FAILED,
            to_state=failed_from_state,
            actor=actor,
            occurred_at=occurred_at,
            retry_action=True,
            approval_remains_valid=approval_remains_valid,
            payload_binding_unchanged=payload_binding_unchanged,
        )
        if retry_transition.occurred_at < self.history[-1].occurred_at:
            raise InvalidStateTransition("transition timestamps must be monotonic")
        return ApprovalStateMachine(
            current_state=failed_from_state,
            history=self.history + (retry_transition,),
        )
