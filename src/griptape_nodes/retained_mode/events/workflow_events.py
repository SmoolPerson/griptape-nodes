from dataclasses import dataclass

from griptape_nodes.node_library.workflow_registry import WorkflowMetadata
from griptape_nodes.retained_mode.events.base_events import (
    RequestPayload,
    ResultPayloadFailure,
    ResultPayloadSuccess,
    WorkflowAlteredMixin,
    WorkflowNotAlteredMixin,
)
from griptape_nodes.retained_mode.events.payload_registry import PayloadRegistry


@dataclass
@PayloadRegistry.register
class RunWorkflowFromScratchRequest(RequestPayload):
    """Run a workflow from file, starting with a clean state.

    Use when: Loading and executing saved workflows, testing workflows from files,
    running workflows in clean environments, batch processing workflows.

    Args:
        file_path: Path to the workflow file to load and execute

    Results: RunWorkflowFromScratchResultSuccess | RunWorkflowFromScratchResultFailure (file not found, load error)
    """

    file_path: str


@dataclass
@PayloadRegistry.register
class RunWorkflowFromScratchResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """Workflow loaded and started successfully from file."""


@dataclass
@PayloadRegistry.register
class RunWorkflowFromScratchResultFailure(ResultPayloadFailure):
    """Workflow execution from file failed. Common causes: file not found, invalid workflow format, load error."""


@dataclass
@PayloadRegistry.register
class RunWorkflowWithCurrentStateRequest(RequestPayload):
    """Run a workflow from file, preserving current state.

    Use when: Loading workflows while keeping existing node values, updating workflow structure
    without losing progress, iterative workflow development.

    Args:
        file_path: Path to the workflow file to load while preserving current state

    Results: RunWorkflowWithCurrentStateResultSuccess | RunWorkflowWithCurrentStateResultFailure (file not found, merge error)
    """

    file_path: str


@dataclass
@PayloadRegistry.register
class RunWorkflowWithCurrentStateResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """Workflow loaded successfully while preserving current state."""


@dataclass
@PayloadRegistry.register
class RunWorkflowWithCurrentStateResultFailure(ResultPayloadFailure):
    """Workflow execution with current state failed. Common causes: file not found, state merge conflict, load error."""


@dataclass
@PayloadRegistry.register
class RunWorkflowFromRegistryRequest(RequestPayload):
    """Run a workflow from the registry.

    Use when: Executing registered workflows, running workflows by name,
    using workflow templates, automated workflow execution.

    Args:
        workflow_name: Name of the workflow in the registry to execute
        run_with_clean_slate: Whether to start with a clean state (default: True)

    Results: RunWorkflowFromRegistryResultSuccess | RunWorkflowFromRegistryResultFailure (workflow not found, execution error)
    """

    workflow_name: str
    run_with_clean_slate: bool = True


@dataclass
@PayloadRegistry.register
class RunWorkflowFromRegistryResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """Workflow from registry started successfully."""


@dataclass
@PayloadRegistry.register
class RunWorkflowFromRegistryResultFailure(ResultPayloadFailure):
    """Workflow execution from registry failed. Common causes: workflow not found, execution error, registry error."""


@dataclass
@PayloadRegistry.register
class RegisterWorkflowRequest(RequestPayload):
    """Register a workflow in the registry.

    Use when: Publishing workflows for reuse, creating workflow templates,
    managing workflow libraries, making workflows available by name.

    Args:
        metadata: Workflow metadata containing name, description, and other properties
        file_name: Name of the workflow file to register

    Results: RegisterWorkflowResultSuccess (with workflow name) | RegisterWorkflowResultFailure (registration error)
    """

    metadata: WorkflowMetadata
    file_name: str


@dataclass
@PayloadRegistry.register
class RegisterWorkflowResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Workflow registered successfully.

    Args:
        workflow_name: Name assigned to the registered workflow
    """

    workflow_name: str


@dataclass
@PayloadRegistry.register
class RegisterWorkflowResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Workflow registration failed. Common causes: invalid metadata, file not found, name conflict."""


@dataclass
@PayloadRegistry.register
class ListAllWorkflowsRequest(RequestPayload):
    """List all workflows in the registry.

    Use when: Displaying workflow catalogs, browsing available workflows,
    implementing workflow selection UIs, workflow management.

    Results: ListAllWorkflowsResultSuccess (with workflows dict) | ListAllWorkflowsResultFailure (registry error)
    """


@dataclass
@PayloadRegistry.register
class ListAllWorkflowsResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Workflows listed successfully.

    Args:
        workflows: Dictionary of workflow names to metadata
    """

    workflows: dict


@dataclass
@PayloadRegistry.register
class ListAllWorkflowsResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Workflow listing failed. Common causes: registry not initialized, registry error."""


@dataclass
@PayloadRegistry.register
class DeleteWorkflowRequest(RequestPayload):
    """Delete a workflow from the registry.

    Use when: Removing obsolete workflows, cleaning up workflow libraries,
    unregistering workflows, workflow management.

    Args:
        name: Name of the workflow to delete from the registry

    Results: DeleteWorkflowResultSuccess | DeleteWorkflowResultFailure (workflow not found, deletion error)
    """

    name: str


@dataclass
@PayloadRegistry.register
class DeleteWorkflowResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """Workflow deleted successfully from registry."""


@dataclass
@PayloadRegistry.register
class DeleteWorkflowResultFailure(ResultPayloadFailure):
    """Workflow deletion failed. Common causes: workflow not found, deletion not allowed, registry error."""


@dataclass
@PayloadRegistry.register
class RenameWorkflowRequest(RequestPayload):
    """Rename a workflow in the registry.

    Use when: Updating workflow names, organizing workflow libraries,
    fixing naming conflicts, workflow management.

    Args:
        workflow_name: Current name of the workflow
        requested_name: New name for the workflow

    Results: RenameWorkflowResultSuccess | RenameWorkflowResultFailure (workflow not found, name conflict)
    """

    workflow_name: str
    requested_name: str


@dataclass
@PayloadRegistry.register
class RenameWorkflowResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """Workflow renamed successfully."""


@dataclass
@PayloadRegistry.register
class RenameWorkflowResultFailure(ResultPayloadFailure):
    """Workflow rename failed. Common causes: workflow not found, name already exists, invalid name."""


@dataclass
@PayloadRegistry.register
class SaveWorkflowRequest(RequestPayload):
    """Save the current workflow to a file.

    Use when: Persisting workflow changes, creating workflow backups,
    exporting workflows, saving before major changes.

    Args:
        file_name: Name of the file to save the workflow to (None for auto-generated)
        image_path: Path to save workflow image/thumbnail (None for no image)

    Results: SaveWorkflowResultSuccess (with file path) | SaveWorkflowResultFailure (save error)
    """

    file_name: str | None = None
    image_path: str | None = None


@dataclass
@PayloadRegistry.register
class ImportWorkflowAsReferencedSubFlowRequest(RequestPayload):
    """Import a workflow as a referenced sub-flow.

    Use when: Reusing workflows as components, creating modular workflows,
    importing workflow templates, building composite workflows.

    Results: ImportWorkflowAsReferencedSubFlowResultSuccess (with flow name) | ImportWorkflowAsReferencedSubFlowResultFailure (import error)
    """

    workflow_name: str
    flow_name: str | None = None  # If None, import into current context flow
    imported_flow_metadata: dict | None = None  # Metadata to apply to the imported flow


@dataclass
@PayloadRegistry.register
class ImportWorkflowAsReferencedSubFlowResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """Workflow imported successfully as referenced sub-flow.

    Args:
        created_flow_name: Name of the created sub-flow
    """

    created_flow_name: str


@dataclass
@PayloadRegistry.register
class ImportWorkflowAsReferencedSubFlowResultFailure(ResultPayloadFailure):
    """Workflow import as sub-flow failed. Common causes: workflow not found, import error, name conflict."""


@dataclass
@PayloadRegistry.register
class SaveWorkflowResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Workflow saved successfully.

    Args:
        file_path: Path where the workflow was saved
    """

    file_path: str


@dataclass
@PayloadRegistry.register
class SaveWorkflowResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Workflow save failed. Common causes: file system error, permission denied, invalid path."""


@dataclass
@PayloadRegistry.register
class LoadWorkflowMetadata(RequestPayload):
    """Load workflow metadata from a file.

    Use when: Inspecting workflow properties, validating workflow files,
    displaying workflow information, workflow management.

    Args:
        file_name: Name of the workflow file to load metadata from

    Results: LoadWorkflowMetadataResultSuccess (with metadata) | LoadWorkflowMetadataResultFailure (load error)
    """

    file_name: str


@dataclass
@PayloadRegistry.register
class LoadWorkflowMetadataResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Workflow metadata loaded successfully.

    Args:
        metadata: Workflow metadata object
    """

    metadata: WorkflowMetadata


@dataclass
@PayloadRegistry.register
class LoadWorkflowMetadataResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Workflow metadata load failed. Common causes: file not found, invalid format, parse error."""


@dataclass
@PayloadRegistry.register
class PublishWorkflowRequest(RequestPayload):
    """Publish a workflow for distribution.

    Use when: Sharing workflows with others, creating workflow packages,
    distributing workflow templates, workflow publishing.

    Results: PublishWorkflowResultSuccess (with file path) | PublishWorkflowResultFailure (publish error)
    """

    workflow_name: str
    publisher_name: str


@dataclass
@PayloadRegistry.register
class PublishWorkflowResultSuccess(ResultPayloadSuccess):
    """Workflow published successfully.

    Args:
        published_workflow_file_path: Path to the published workflow file
    """

    published_workflow_file_path: str


@dataclass
@PayloadRegistry.register
class PublishWorkflowResultFailure(ResultPayloadFailure):
    """Workflow publish failed. Common causes: workflow not found, publish error, file system error."""
