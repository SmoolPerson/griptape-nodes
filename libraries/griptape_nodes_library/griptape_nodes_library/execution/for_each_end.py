from typing import Any

from griptape_nodes.exe_types.core_types import (
    ControlParameterInput,
    ControlParameterOutput,
    Parameter,
    ParameterMode,
    ParameterTypeBuiltin,
)
from griptape_nodes.exe_types.node_types import BaseNode, EndLoopNode, StartLoopNode


class ForEachEndNode(EndLoopNode):
    """For Each End Node that completes a loop iteration and connects back to the ForEachStartNode.

    This node marks the end of a loop body and signals the ForEachStartNode to continue with the next item
    or to complete the loop if all items have been processed.

    CONDITIONAL DEPENDENCY RESOLUTION:
    This node implements conditional evaluation similar to the IfElse pattern.
    We will ONLY evaluate the current item Parameter if we enter into the node via "Add Item to Output".
    This prevents unnecessary computation when taking alternative control paths like "Skip" or "Break".
    """

    output: Parameter

    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        super().__init__(name, metadata)
        self.start_node = None

        # ForEach End manages its own results list
        self._results_list: list[Any] = []

        # Connection tracking for validation
        self._connected_parameters: set[str] = set()

        # Explicit tethering to ForEachStart node
        self.from_start = Parameter(
            name="from_start",
            tooltip="Connected ForEach Start Node",
            input_types=[ParameterTypeBuiltin.ALL.value],
            allowed_modes={ParameterMode.INPUT},
        )
        self.from_start.ui_options = {"hide": True, "display_name": "Loop Start Node"}

        # Main control input and data parameter
        self.add_item_control = ControlParameterInput(
            tooltip="Add current item to output and continue loop", name="add_item"
        )
        self.add_item_control.ui_options = {"display_name": "Add Item to Output"}

        # Data input for the item to add - positioned right under Add Item control
        self.new_item_to_add = Parameter(
            name="new_item_to_add",
            tooltip="Item to add to results list",
            type=ParameterTypeBuiltin.ANY.value,
            allowed_modes={ParameterMode.INPUT},
        )

        # Loop completion output
        self.exec_out = ControlParameterOutput(tooltip="Triggered when loop completes", name="exec_out")
        self.exec_out.ui_options = {"display_name": "On Loop Complete"}

        # Results output - positioned below On Loop Complete
        self.results = Parameter(
            name="results",
            tooltip="Collected loop results",
            output_type="list",
            allowed_modes={ParameterMode.OUTPUT},
        )

        # Advanced control options for skip and break
        self.skip_control = ControlParameterInput(
            tooltip="Skip current item and continue to next iteration", name="skip_iteration"
        )
        self.skip_control.ui_options = {"display_name": "Skip to Next Iteration"}

        self.break_control = ControlParameterInput(tooltip="Break out of loop immediately", name="break_loop")
        self.break_control.ui_options = {"display_name": "Break Out of Loop"}

        # Hidden inputs from ForEachStart

        self.loop_end_condition_met_signal_input = ControlParameterInput(
            tooltip="Signal from ForEachStart when loop should end", name="loop_end_condition_met_signal_input"
        )
        self.loop_end_condition_met_signal_input.ui_options = {"hide": True, "display_name": "Loop End Signal Input"}
        self.loop_end_condition_met_signal_input.settable = False

        # Hidden outputs to ForEachStart
        self.trigger_next_iteration_signal_output = ControlParameterOutput(
            tooltip="Signal to ForEachStart to continue to next iteration", name="trigger_next_iteration_signal_output"
        )
        self.trigger_next_iteration_signal_output.ui_options = {
            "hide": True,
            "display_name": "Next Iteration Signal Output",
        }
        self.trigger_next_iteration_signal_output.settable = False

        self.break_loop_signal_output = ControlParameterOutput(
            tooltip="Signal to ForEachStart to break out of loop", name="break_loop_signal_output"
        )
        self.break_loop_signal_output.ui_options = {"hide": True, "display_name": "Break Loop Signal Output"}
        self.break_loop_signal_output.settable = False

        # Add main workflow parameters first
        self.add_parameter(self.add_item_control)
        self.add_parameter(self.new_item_to_add)
        self.add_parameter(self.exec_out)
        self.add_parameter(self.results)

        # Add advanced control options before tethering connection
        self.add_parameter(self.skip_control)
        self.add_parameter(self.break_control)

        # Add hidden parameters
        self.add_parameter(self.from_start)
        self.add_parameter(self.loop_end_condition_met_signal_input)
        self.add_parameter(self.trigger_next_iteration_signal_output)
        self.add_parameter(self.break_loop_signal_output)

    def validate_before_node_run(self) -> list[Exception] | None:
        # Don't clear results list here - we need to accumulate across loop iterations
        exceptions = []
        if self.start_node is None:
            exceptions.append(Exception("Start node is not set on End Node."))

        # Validate all required connections exist
        validation_errors = self._validate_foreach_connections()
        if validation_errors:
            exceptions.extend(validation_errors)

        if exceptions:
            return exceptions
        return super().validate_before_node_run()

    def validate_before_workflow_run(self) -> list[Exception] | None:
        # Don't reset here - let reset_for_workflow_run() handle it to avoid conflicts
        exceptions = []
        if self.start_node is None:
            exceptions.append(Exception("Start node is not set on End Node."))

        # Validate all required connections exist
        validation_errors = self._validate_foreach_connections()
        if validation_errors:
            exceptions.extend(validation_errors)

        if exceptions:
            return exceptions
        return super().validate_before_node_run()

    def process(self) -> None:
        # Determine which control input was used to enter this node
        # CONDITIONAL EVALUATION: We only process the new_item_to_add if we entered via "Add Item to Output"
        # This prevents unnecessary computation when taking Skip or Break paths

        match self._entry_control_parameter:
            case self.add_item_control:
                # Only evaluate new_item_to_add parameter when adding to output
                new_item_value = self.get_parameter_value("new_item_to_add")
                self._results_list.append(new_item_value)
            case self.skip_control:
                # Skip - don't add anything to output, just continue loop
                pass
            case self.break_control:
                # Break - will trigger break signal in get_next_control_output
                pass
            case self.loop_end_condition_met_signal_input:
                # Loop has ended naturally, output final results
                self.parameter_output_values["results"] = self._results_list.copy()
                return

        # Always output the current results list state
        self.parameter_output_values["results"] = self._results_list.copy()

    def get_next_control_output(self) -> Parameter | None:
        """Return the appropriate signal output based on the control path taken.

        This triggers the correct signal back to ForEachStart to manage loop flow.
        """
        match self._entry_control_parameter:
            case self.add_item_control | self.skip_control:
                # Both add and skip trigger next iteration
                return self.trigger_next_iteration_signal_output
            case self.break_control:
                # Break triggers break loop signal
                return self.break_loop_signal_output
            case self.loop_end_condition_met_signal_input:
                # Loop end condition triggers normal completion
                return self.exec_out
            case _:
                # Default fallback - should not happen
                return self.exec_out

    def _validate_foreach_connections(self) -> list[Exception]:
        """Validate that all required ForEach connections are properly established.

        Returns a list of validation errors with detailed instructions for the user.
        """
        errors = []

        # Check if from_start has incoming connection from ForEach Start
        if self.start_node is None:
            errors.append(
                Exception(
                    f"{self.name}: Missing required tethering connection. "
                    "REQUIRED ACTION: Connect ForEach Start 'Loop End Node' to ForEach End 'Loop Start Node'. "
                    "This establishes the explicit relationship between start and end nodes."
                )
            )

        # Check if all hidden signal connections exist (only if start_node is connected)
        if self.start_node and "loop_end_condition_met_signal_input" not in self._connected_parameters:
            errors.append(
                Exception(
                    f"{self.name}: Missing hidden signal connection. "
                    "REQUIRED ACTION: Connect ForEach Start 'Loop End Signal' to ForEach End 'Loop End Signal Input'. "
                    "This receives the signal when the loop has completed naturally."
                )
            )

            # Note: outgoing connections tracked via start_node relationship

        # Check if control inputs have at least one connection
        control_names = ["add_item", "skip_iteration", "break_loop"]
        connected_controls = [name for name in control_names if name in self._connected_parameters]

        if not connected_controls:
            errors.append(
                Exception(
                    f"{self.name}: No control flow connections found. "
                    "REQUIRED ACTION: Connect at least one control flow to ForEach End. "
                    "Options: 'Add Item to Output', 'Skip to Next Iteration', or 'Break Out of Loop'. "
                    "The ForEach End needs to receive control flow from your loop body logic."
                )
            )

        return errors

    def after_incoming_connection(
        self,
        source_node: BaseNode,
        source_parameter: Parameter,
        target_parameter: Parameter,
    ) -> None:
        # Track incoming connections for validation
        self._connected_parameters.add(target_parameter.name)

        if target_parameter is self.from_start and isinstance(source_node, StartLoopNode):
            self.start_node = source_node
            # Auto-create all hidden signal connections when main tethering connection is made
            self._create_hidden_signal_connections(source_node)
        return super().after_incoming_connection(source_node, source_parameter, target_parameter)

    def after_incoming_connection_removed(
        self,
        source_node: BaseNode,
        source_parameter: Parameter,
        target_parameter: Parameter,
    ) -> None:
        # Remove from tracking when connection is removed
        self._connected_parameters.discard(target_parameter.name)

        if target_parameter is self.from_start and isinstance(source_node, StartLoopNode):
            self.start_node = None
            # Clean up hidden signal connections when main tethering connection is removed
            self._remove_hidden_signal_connections(source_node)
        return super().after_incoming_connection_removed(source_node, source_parameter, target_parameter)

    def _create_hidden_signal_connections(self, start_node: BaseNode) -> None:
        """Automatically create all hidden signal connections between ForEach Start and End nodes.

        This method is called when the main tethering connection (from_start) is established.
        It creates all the required hidden connections for the ForEach loop to function properly.
        """
        from griptape_nodes.retained_mode.events.connection_events import CreateConnectionRequest
        from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

        # Create the hidden signal connections and default control flow for ForEach loop functionality:

        # 1. Start → End: loop_end_condition_met_signal → loop_end_condition_met_signal_input
        GriptapeNodes.handle_request(
            CreateConnectionRequest(
                source_node_name=start_node.name,
                source_parameter_name="loop_end_condition_met_signal",
                target_node_name=self.name,
                target_parameter_name="loop_end_condition_met_signal_input",
            )
        )

        # 2. End → Start: trigger_next_iteration_signal_output → trigger_next_iteration_signal
        GriptapeNodes.handle_request(
            CreateConnectionRequest(
                source_node_name=self.name,
                source_parameter_name="trigger_next_iteration_signal_output",
                target_node_name=start_node.name,
                target_parameter_name="trigger_next_iteration_signal",
            )
        )

        # 3. End → Start: break_loop_signal_output → break_loop_signal
        GriptapeNodes.handle_request(
            CreateConnectionRequest(
                source_node_name=self.name,
                source_parameter_name="break_loop_signal_output",
                target_node_name=start_node.name,
                target_parameter_name="break_loop_signal",
            )
        )

        # 4. Default control flow: Start → End: exec_out → add_item (default "happy path")
        # Only create this connection if the exec_out parameter doesn't already have a connection
        connections = GriptapeNodes.FlowManager().get_connections()
        existing_connections = connections.outgoing_index.get(start_node.name, {}).get("exec_out", [])

        if not existing_connections:
            GriptapeNodes.handle_request(
                CreateConnectionRequest(
                    source_node_name=start_node.name,
                    source_parameter_name="exec_out",
                    target_node_name=self.name,
                    target_parameter_name="add_item",
                )
            )

    def _remove_hidden_signal_connections(self, start_node: BaseNode) -> None:
        """Remove all hidden signal connections when the main tethering connection is removed.

        This method cleans up the hidden connections when the ForEach Start and End nodes
        are disconnected via the main tethering connection.
        """
        # Remove the hidden signal connections and default control flow:
        # Note: Check if connections exist before attempting deletion to avoid error messages
        from griptape_nodes.retained_mode.events.connection_events import (
            DeleteConnectionRequest,
            ListConnectionsForNodeRequest,
            ListConnectionsForNodeResultSuccess,
        )
        from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

        # Get current connections for start node to check what still exists
        list_connections_result = GriptapeNodes.handle_request(ListConnectionsForNodeRequest(node_name=start_node.name))
        if not isinstance(list_connections_result, ListConnectionsForNodeResultSuccess):
            return  # Cannot determine what connections exist, exit gracefully

        # Helper function to check if a connection exists
        def connection_exists(source_node: str, source_param: str, target_node: str, target_param: str) -> bool:
            # Check in outgoing connections from source node
            for conn in list_connections_result.outgoing_connections:
                if (
                    conn.source_parameter_name == source_param
                    and conn.target_node_name == target_node
                    and conn.target_parameter_name == target_param
                ):
                    return True
            # Check in incoming connections to source node
            for conn in list_connections_result.incoming_connections:
                if (
                    conn.source_node_name == source_node
                    and conn.source_parameter_name == source_param
                    and conn.target_parameter_name == target_param
                ):
                    return True
            return False

        # 1. Start → End: loop_end_condition_met_signal → loop_end_condition_met_signal_input
        if connection_exists(
            start_node.name, "loop_end_condition_met_signal", self.name, "loop_end_condition_met_signal_input"
        ):
            GriptapeNodes.handle_request(
                DeleteConnectionRequest(
                    source_node_name=start_node.name,
                    source_parameter_name="loop_end_condition_met_signal",
                    target_node_name=self.name,
                    target_parameter_name="loop_end_condition_met_signal_input",
                )
            )

        # 2. End → Start: trigger_next_iteration_signal_output → trigger_next_iteration_signal
        if connection_exists(
            self.name, "trigger_next_iteration_signal_output", start_node.name, "trigger_next_iteration_signal"
        ):
            GriptapeNodes.handle_request(
                DeleteConnectionRequest(
                    source_node_name=self.name,
                    source_parameter_name="trigger_next_iteration_signal_output",
                    target_node_name=start_node.name,
                    target_parameter_name="trigger_next_iteration_signal",
                )
            )

        # 3. End → Start: break_loop_signal_output → break_loop_signal
        if connection_exists(self.name, "break_loop_signal_output", start_node.name, "break_loop_signal"):
            GriptapeNodes.handle_request(
                DeleteConnectionRequest(
                    source_node_name=self.name,
                    source_parameter_name="break_loop_signal_output",
                    target_node_name=start_node.name,
                    target_parameter_name="break_loop_signal",
                )
            )

        # NOTE: We do NOT automatically delete the default control flow connection
        # (Start exec_out → End add_item) because it's a visible connection that users
        # may have intentionally kept, modified, or replaced with custom logic.
        # Unlike the hidden signal connections above, this is user-controllable.

    def initialize_spotlight(self) -> None:
        """Custom spotlight initialization for conditional dependency resolution.

        Similar to the IfElse pattern, we only include the new_item_to_add parameter
        in the dependency chain if we entered via the "Add Item to Output" control path.

        BIG COMMENT FOR FUTURE ARCHAEOLOGY:
        This method prevents the automatic resolution of the new_item_to_add parameter
        when the node is entered via "Skip to Next Iteration" or "Break Out of Loop".
        This is crucial for performance - we don't want to evaluate expensive upstream
        computations if we're just going to skip the item anyway.

        The conditional logic works by:
        1. Checking which control input was used to enter this node
        2. Only adding new_item_to_add to the spotlight dependency chain if we entered via "Add Item to Output"
        3. This mirrors the pattern established in the IfElse node for conditional branch evaluation
        """
        match self._entry_control_parameter:
            case self.add_item_control:
                # Only resolve new_item_to_add dependency if we're actually going to use it
                new_item_param = self.get_parameter_by_name("new_item_to_add")
                if new_item_param and ParameterMode.INPUT in new_item_param.get_mode():
                    self.current_spotlight_parameter = new_item_param
            case _:
                # For skip or break paths, don't resolve any input dependencies
                self.current_spotlight_parameter = None

    def advance_parameter(self) -> bool:
        """Custom parameter advancement with conditional dependency resolution.

        This ensures we only resolve parameters that are actually needed based on
        the control path taken to enter this node.
        """
        if self.current_spotlight_parameter is None:
            return False

        # Use default advancement behavior for the new_item_to_add parameter
        if self.current_spotlight_parameter.next is not None:
            self.current_spotlight_parameter = self.current_spotlight_parameter.next
            return True

        self.current_spotlight_parameter = None
        return False

    def reset_for_workflow_run(self) -> None:
        """Reset ForEach End state for a fresh workflow run."""
        self._results_list = []
