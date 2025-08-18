from typing import Any

from griptape_nodes.exe_types.core_types import (
    Parameter,
)
from griptape_nodes.exe_types.node_types import DataNode
import os

class ListFiles(DataNode):
    def __init__(
        self,
        name: str,
        metadata: dict[Any, Any] | None = None,
        value: str = "",
    ) -> None:
        super().__init__(name, metadata)

        # Add output parameter for the string
        self.add_parameter(
            Parameter(
                name="Directory",
                default_value=value,
                input_types=["str"],
                type="str",
                tooltip="The directory to list files in",
                ui_options={"multiline": True},
            )
        )
        self.add_parameter(
            Parameter(
                name="Files",
                default_value=value,
                output_type="list[str]",
                type="list[str]",
                tooltip="The files in the directory",
                ui_options={"multiline": True},
            )
        )

    def process(self) -> None:
        # List files in the specified directory, giving errors if the directory does not exist
        try:
            files = os.listdir(self.get_parameter_value("Directory"))
        except Exception as e:
            raise RuntimeError(f"Listing files failed due to error: {str(e)}")
        self.parameter_output_values["Files"] = files
