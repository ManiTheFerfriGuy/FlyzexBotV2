"""Application form definition utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

from flyzexbot.localization import (
    AVAILABLE_LANGUAGE_CODES,
    DEFAULT_LANGUAGE_CODE,
    TextPack,
    get_default_text_pack,
    get_text_pack,
)


@dataclass(slots=True)
class QuestionOption:
    """Represents a selectable option for a choice question."""

    value: str
    label: str
    aliases: tuple[str, ...] = ()

    def matches(self, answer: str) -> bool:
        """Return ``True`` if *answer* matches this option by value, label or alias."""

        if not answer:
            return False
        normalised = answer.casefold()
        if normalised == self.value.casefold():
            return True
        if normalised == self.label.casefold():
            return True
        return any(normalised == alias.casefold() for alias in self.aliases)

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "label": self.label,
            "aliases": list(self.aliases),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "QuestionOption":
        value = str(payload.get("value", "")).strip()
        label = str(payload.get("label", "")).strip()
        aliases_payload = payload.get("aliases", [])
        aliases: tuple[str, ...]
        if isinstance(aliases_payload, (list, tuple)):
            aliases = tuple(
                str(item).strip() for item in aliases_payload if str(item).strip()
            )
        else:
            aliases = ()
        return cls(value=value, label=label or value, aliases=aliases)


@dataclass(slots=True)
class ApplicationQuestionDefinition:
    """Represents a single question shown during the application flow."""

    question_id: str
    prompt: str
    kind: str = "text"
    order: int = 0
    required: bool = True
    title: str | None = None
    options: tuple[QuestionOption, ...] = field(default_factory=tuple)
    depends_on: str | None = None
    depends_value: str | None = None

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "prompt": self.prompt,
            "kind": self.kind,
            "order": self.order,
            "required": self.required,
            "title": self.title,
            "options": [option.to_dict() for option in self.options],
            "depends_on": self.depends_on,
            "depends_value": self.depends_value,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "ApplicationQuestionDefinition":
        question_id = str(payload.get("question_id", "")).strip()
        prompt = str(payload.get("prompt", "")).strip()
        kind = str(payload.get("kind", "text")).strip().casefold() or "text"
        if kind not in {"text", "choice"}:
            kind = "text"
        try:
            order = int(payload.get("order", 0))
        except (TypeError, ValueError):
            order = 0
        required = bool(payload.get("required", True))
        title_payload = payload.get("title")
        title = str(title_payload).strip() if isinstance(title_payload, str) else None
        options_payload = payload.get("options", [])
        options: tuple[QuestionOption, ...]
        if isinstance(options_payload, Iterable):
            options = tuple(
                QuestionOption.from_dict(option)
                for option in options_payload
                if isinstance(option, dict)
            )
        else:
            options = tuple()
        depends_on_payload = payload.get("depends_on")
        depends_value_payload = payload.get("depends_value")
        depends_on = (
            str(depends_on_payload).strip()
            if isinstance(depends_on_payload, str)
            else None
        )
        depends_value = (
            str(depends_value_payload).strip()
            if isinstance(depends_value_payload, str)
            else None
        )
        return cls(
            question_id=question_id,
            prompt=prompt,
            kind=kind,
            order=order,
            required=required,
            title=title,
            options=options,
            depends_on=depends_on,
            depends_value=depends_value,
        )

    def with_prompt(self, prompt: str) -> "ApplicationQuestionDefinition":
        return ApplicationQuestionDefinition(
            question_id=self.question_id,
            prompt=prompt,
            kind=self.kind,
            order=self.order,
            required=self.required,
            title=self.title,
            options=self.options,
            depends_on=self.depends_on,
            depends_value=self.depends_value,
        )


def _build_role_question(
    texts: TextPack, *, order: int
) -> ApplicationQuestionDefinition:
    options: list[QuestionOption] = []
    for value, synonyms in texts.dm_application_role_options.items():
        labels = [str(item).strip() for item in synonyms if str(item).strip()]
        if not labels:
            label = value
            aliases: tuple[str, ...] = ()
        else:
            label = labels[0]
            aliases = tuple(labels)
        options.append(QuestionOption(value=value, label=label, aliases=aliases))
    return ApplicationQuestionDefinition(
        question_id="role",
        prompt=texts.dm_application_role_prompt,
        kind="choice",
        order=order,
        title=texts.dm_admin_questions_role_label,
        options=tuple(options),
    )


def _build_followup_questions(
    texts: TextPack,
    *,
    start_order: int,
) -> List[ApplicationQuestionDefinition]:
    definitions: list[ApplicationQuestionDefinition] = []
    order = start_order
    template = getattr(texts, "dm_admin_questions_followup_label_template", "{role}")
    for value, prompt in texts.dm_application_followup_prompts.items():
        role_options = texts.dm_application_role_options.get(value, [])
        label = role_options[0] if role_options else value
        definitions.append(
            ApplicationQuestionDefinition(
                question_id=f"followup_{value}",
                prompt=prompt,
                kind="text",
                order=order,
                title=template.format(role=label),
                depends_on="role",
                depends_value=value,
            )
        )
        order += 1
    return definitions


def _build_free_text_question(
    question_id: str,
    prompt: str,
    title: str,
    *,
    order: int,
) -> ApplicationQuestionDefinition:
    return ApplicationQuestionDefinition(
        question_id=question_id,
        prompt=prompt,
        kind="text",
        order=order,
        title=title,
    )


def build_default_form(
    language_code: str | None = None,
) -> List[ApplicationQuestionDefinition]:
    """Return the default form definition for the provided language."""

    normalised = (language_code or "").strip().lower()
    if normalised in AVAILABLE_LANGUAGE_CODES:
        texts = get_text_pack(normalised)
    else:
        texts = get_default_text_pack()

    order = 1
    definitions: list[ApplicationQuestionDefinition] = [
        _build_role_question(texts, order=order)
    ]
    order += 1

    followups = _build_followup_questions(texts, start_order=order)
    definitions.extend(followups)
    order += len(followups)

    definitions.append(
        _build_free_text_question(
            "goals",
            texts.dm_application_goals_prompt,
            texts.dm_admin_questions_goals_label,
            order=order,
        )
    )
    order += 1

    definitions.append(
        _build_free_text_question(
            "availability",
            texts.dm_application_availability_prompt,
            texts.dm_admin_questions_availability_label,
            order=order,
        )
    )

    return definitions


def serialise_form(definitions: Sequence[ApplicationQuestionDefinition]) -> List[dict]:
    return [definition.to_dict() for definition in definitions]


def parse_form(payload: Iterable[dict]) -> List[ApplicationQuestionDefinition]:
    definitions: list[ApplicationQuestionDefinition] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        definition = ApplicationQuestionDefinition.from_dict(item)
        if not definition.question_id:
            continue
        definitions.append(definition)
    definitions.sort(key=lambda definition: (definition.order, definition.question_id))
    return definitions


def ensure_ordering(
    definitions: Sequence[ApplicationQuestionDefinition],
) -> List[ApplicationQuestionDefinition]:
    ordered = sorted(
        definitions, key=lambda definition: (definition.order, definition.question_id)
    )
    current = 1
    normalised: list[ApplicationQuestionDefinition] = []
    for definition in ordered:
        normalised.append(
            ApplicationQuestionDefinition(
                question_id=definition.question_id,
                prompt=definition.prompt,
                kind=definition.kind,
                order=current,
                required=definition.required,
                title=definition.title,
                options=definition.options,
                depends_on=definition.depends_on,
                depends_value=definition.depends_value,
            )
        )
        current += 1
    return normalised
