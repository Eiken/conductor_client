"""Entry point for conductor nodes.

There are 2 types of node conductor node in the HDA (Houdini digital Asset)

conductor::job
conductor::submitter

This module handles callbacks and other actions from those nodes.

This includes handling all actions from widgets, aux buttons
as well as populating menus, initializing state and so on.

Attributes:
    ACTIONS (dict): Mapping of parm_names to callbacks they trigger.
    AUX_BUTTON_ACTIONS (dict): Mapping of auxilary buttons to callbacks
    MENUS (dict): Mapping of callbacks to populate menus dynamically
"""

import traceback
import hou

from conductor.houdini.lib import data_block
from conductor.houdini.hda import (
    instances_ui,
    projects_ui,
    frame_spec_ui,
    driver_ui,
    job_source_ui,
    action_row_ui,
    software_ui,
    notifications_ui,
    submission_ui,
    takes,
    uistate,
    types
)

def _all_job_nodes():
    return hou.nodeType(hou.ropNodeTypeCategory(), "conductor::job::0.1").instances()

def _all_submitter_nodes():
    return hou.nodeType(hou.ropNodeTypeCategory(), "conductor::submitter::0.1").instances()

def force_update(node, **_):
    """Update was called from the job node UI."""
    db = data_block.for_houdini(force=True)

    for job in _all_job_nodes():
        _update_job_node(job)

    for submitter in _all_submitter_nodes():
        _update_submitter_node(submitter)

def _update_submitter_node(node, **_):
    """Initialize or update.

    We do this on creation/loading or manually. We do it in
    the root take context to ensure everything is unlocked.
    This can be called without the expensive
    force_update, but still update widgets
    """
    with takes.take_context(hou.takes.rootTake()):
        job_source_ui.update_inputs(node)
        notifications_ui.validate_emails(node)
        notifications_ui.email_hook_changed(node)
        submission_ui.on_toggle_timestamped_scene(node)
        uistate.update_button_state(node)


def _update_job_node(node, **_):
    """Initialize or update.

    We do this on creation/loading or manually. We do it in
    the root take context to ensure everything is unlocked.

    This can be called without the expensive
    force_update, but still update widgets
    """

    with takes.take_context(hou.takes.rootTake()):

        frame_spec_ui.validate_custom_range(node)
        frame_spec_ui.validate_scout_range(node)
        frame_spec_ui.set_type(node)
        driver_ui.update_input_node(node)
        submission_ui.on_toggle_timestamped_scene(node)
        notifications_ui.validate_emails(node)
        notifications_ui.email_hook_changed(node)
        uistate.update_button_state(node)


def _initialize_job_node(node, **_):
    """On creation only, set some defaults in software UI."""
    with takes.take_context(hou.takes.rootTake()):
        software_ui.initialize(node)


MENUS = dict(
    machine_type=instances_ui.populate_menu,
    project=projects_ui.populate_menu
)


ACTIONS = dict(
    source=driver_ui.update_input_type,
    preview=action_row_ui.preview,
    submit=action_row_ui.submit,
    update=force_update,
    use_custom=frame_spec_ui.set_type,
    fs1=frame_spec_ui.on_frame_range_changed,
    fs2=frame_spec_ui.on_frame_range_changed,
    fs3=frame_spec_ui.on_frame_range_changed,
    custom_range=frame_spec_ui.validate_custom_range,
    clump_size=frame_spec_ui.on_clump_size_changed,
    do_scout=frame_spec_ui.on_do_scout_changed,
    scout_frames=frame_spec_ui.validate_scout_range,
    detect_software=software_ui.detect,
    choose_software=software_ui.choose,
    clear_software=software_ui.on_clear,
    project=projects_ui.select,
    email_addresses=notifications_ui.validate_emails,
    email_on_submit=notifications_ui.email_hook_changed,
    email_on_start=notifications_ui.email_hook_changed,
    email_on_finish=notifications_ui.email_hook_changed,
    email_on_failure=notifications_ui.email_hook_changed,
    use_timestamped_scene=submission_ui.on_toggle_timestamped_scene
)

AUX_BUTTON_ACTIONS = dict(
    clump_size=frame_spec_ui.best_clump_size
)


def populate_menu(node, parm, **_):
    """Populate a menu dynamically.

    Houdini requires the token value pairs for menu item
    creation to be a flattened list like so: [k0, v0, k1,
    v2, ... kn, vn]
    """
    try:
        return MENUS[parm.name()](node)
    except hou.Error as err:
        hou.ui.displayMessage(title='Error', text=err.instanceMessage(),
                              details_label="Show stack trace",
                              details=traceback.format_exc(),
                              severity=hou.severityType.Error)


def action_callback(**kwargs):
    """Lookup callback in `ACTIONS` registry.

    Uses the parm_name kw arg provided by houdini to
    differentiate.
    """

    try:
        ACTIONS[kwargs['parm_name']](**kwargs)
    except hou.InvalidInput as err:
        hou.ui.displayMessage(title='Error', text=err.instanceMessage(),
                              details_label="Show stack trace",
                              details=traceback.format_exc(),
                              severity=hou.severityType.ImportantMessage)
    except hou.Error as err:
        hou.ui.displayMessage(title='Error', text=err.instanceMessage(),
                              details_label="Show stack trace",
                              details=traceback.format_exc(),
                              severity=hou.severityType.Error)

    except(TypeError, ValueError) as err:
        hou.ui.displayMessage(title='Error', text=str(err),
                              details_label="Show stack trace",
                              details=traceback.format_exc(),
                              severity=hou.severityType.Error)

    except(Exception) as err:
        hou.ui.displayMessage(title='Error', text=str(err),
                              details_label="Show stack trace",
                              details=traceback.format_exc(),
                              severity=hou.severityType.Error)


def action_button_callback(**kwargs):
    """Handle actions triggered by the little buttons next to params.

    Uses the parmtuple kw arg provided by houdini to
    determine the parm this button refers to.
    """
    try:
        AUX_BUTTON_ACTIONS[kwargs['parmtuple'].name()](**kwargs)
    except hou.Error as err:
        hou.ui.displayMessage(title='Error', text=err.instanceMessage(),
                              details_label="Show stack trace",
                              details=traceback.format_exc(),
                              severity=hou.severityType.Error)


def on_input_changed_callback(node, **_):
    """Make changes based on input connecion make/break."""
    try:
        if types.is_job_node(node):
            driver_ui.update_input_node(node)
        else:
            job_source_ui.update_inputs(node)

    except hou.Error as err:
        hou.ui.displayMessage(title='Error', text=err.instanceMessage(),
                              details_label="Show stack trace",
                              details=traceback.format_exc(),
                              severity=hou.severityType.Error)


def _on_created_or_loaded(node):
    """Update things when a node is created or loaded."""
    if types.is_job_node(node):
        _update_job_node(node)
    else:
        _update_submitter_node(node)


def _on_created(node):
    """Update things when a node is created only."""
    if types.is_job_node(node):
        _initialize_job_node(node)


def on_created_callback(node, **_):
    """Initialize state when a node is created."""
    try:
        _on_created_or_loaded(node)
        _on_created(node)
    except hou.Error as err:
        hou.ui.displayMessage(title='Error', text=err.instanceMessage(),
                              details_label="Show stack trace",
                              details=traceback.format_exc(),
                              severity=hou.severityType.Error)


def on_loaded_callback(node, **_):
    """Initialize state when a node is loaded."""
    try:
        _on_created_or_loaded(node)
    except hou.Error as err:
        hou.ui.displayMessage(title='Error', text=err.instanceMessage(),
                              details_label="Show stack trace",
                              details=traceback.format_exc(),
                              severity=hou.severityType.Error)