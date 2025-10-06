from __future__ import annotations

from dataclasses import fields
from typing import Any

from flyzexbot.localization import TextPack, PERSIAN_TEXTS, ENGLISH_TEXTS


def test_textpack_fields_exist_in_both_languages() -> None:
    fa = PERSIAN_TEXTS
    en = ENGLISH_TEXTS

    for f in fields(TextPack):
        name = f.name
        assert hasattr(fa, name), f"Persian TextPack missing field: {name}"
        assert hasattr(en, name), f"English TextPack missing field: {name}"

        fa_value: Any = getattr(fa, name)
        en_value: Any = getattr(en, name)

        # For dict-like fields, ensure key parity across languages
        if isinstance(fa_value, dict) and isinstance(en_value, dict):
            assert set(fa_value.keys()) == set(en_value.keys()), (
                f"Dictionary key mismatch for '{name}':\n"
                f"FA-only: {set(fa_value.keys()) - set(en_value.keys())}\n"
                f"EN-only: {set(en_value.keys()) - set(fa_value.keys())}"
            )
        else:
            # For scalar values (mostly strings), ensure they are present
            assert fa_value is not None, f"Persian value missing for field: {name}"
            assert en_value is not None, f"English value missing for field: {name}"


def test_role_and_followup_option_keys_match() -> None:
    # Explicitly verify core option maps are aligned between languages
    fa_roles = PERSIAN_TEXTS.dm_application_role_options
    en_roles = ENGLISH_TEXTS.dm_application_role_options
    assert set(fa_roles.keys()) == set(en_roles.keys()), "Role option keys differ between FA and EN"

    fa_followups = PERSIAN_TEXTS.dm_application_followup_prompts
    en_followups = ENGLISH_TEXTS.dm_application_followup_prompts
    assert set(fa_followups.keys()) == set(en_followups.keys()), "Follow-up prompt keys differ between FA and EN"
