# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Utilities for checking and displaying update notifications."""

from __future__ import annotations

import logging
from dataclasses import dataclass

try:
    from deadline.client.api import safe_check_for_updates, UpdateCheckResult, UpdateCheckStatus
    from deadline.client.ui.dialogs.update_available_dialog import UpdateAvailableDialog

    _UPDATE_CHECK_AVAILABLE = True
except ImportError:
    # Older bundled deadline-cloud libraries (e.g. an install updated via a
    # partial file sync rather than the full installer) don't ship the
    # update-check API. Degrade gracefully so importing the submitter doesn't
    # crash; the update-notification feature is simply disabled.
    _UPDATE_CHECK_AVAILABLE = False

from ._version import version_tuple as adaptor_version_tuple
from .style import C4D_STYLE

logger = logging.getLogger(__name__)


@dataclass
class _SessionState:
    """Session-level state: once the user dismisses the update dialog,
    don't show it again until Cinema 4D is restarted."""

    update_dismissed: bool = False


_session_state = _SessionState()


def _check_for_update() -> UpdateCheckResult:
    """Check if a newer version of the Cinema 4D submitter is available.

    Returns:
        An UpdateCheckResult describing whether an update is available.
    """
    current_version = ".".join(str(v) for v in adaptor_version_tuple[:3])
    return safe_check_for_updates(
        integration_name="deadline-cloud-for-cinema-4d",
        current_version=current_version,
    )


def check_and_show_update_dialog() -> bool:
    """Check for updates and show the update dialog if one is available.

    If the user previously dismissed the dialog in this Cinema 4D session,
    the check is skipped entirely.

    Returns:
        True if the user clicked Download (caller should skip opening the submitter),
        False otherwise.
    """
    if not _UPDATE_CHECK_AVAILABLE:
        # Installed deadline-cloud library is too old to support update checks.
        return False

    if _session_state.update_dismissed:
        return False

    update_result = _check_for_update()
    if update_result.status == UpdateCheckStatus.SUCCESS and update_result.update_available:
        update_dialog = UpdateAvailableDialog(
            integration_name="Cinema 4D",
            current_version=update_result.current_version or "",
            latest_version=update_result.latest_version or "",
            download_url=update_result.download_url or "",
            release_notes_url="https://github.com/aws-deadline/deadline-cloud-for-cinema-4d/releases",
        )
        update_dialog.setStyleSheet(C4D_STYLE)
        update_dialog.exec_()
        if update_dialog.user_downloaded:
            return True
        # User dismissed — suppress for the rest of this Cinema 4D session
        _session_state.update_dismissed = True
    return False
