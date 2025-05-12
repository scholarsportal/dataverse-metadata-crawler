"""ExportManager class for managing JSON exports with descriptions and tracking."""
from utils import orjson_export
from custom_logging import CustomLogger


logger = CustomLogger.get_logger(__name__)


class ExportManager:
    """Class to manage JSON exports with predefined descriptions and tracking."""
    # Preset descriptions for different export types
    DESCRIPTIONS = {
        'pid_dict_dd': 'Hierarchical Information of Datasets(deaccessioned/draft)',
        'failed_metadata_uris': 'PIDs of Datasets Failed to be crawled (Representation & File)',
        'permission_dict': 'Dataset Metadata (Permission)',
        'pid_dict': 'Hierarchical Information of Datasets',
        'ds_metadata': 'Dataset Metadata (Representation, File & Permission)',
        'empty_dv': 'Empty Dataverses',
        'spreadsheet': 'Dataset Metadata CSV',
    }

    def __init__(self) -> None:
        """Initialize the export manager."""
        self.tracking_dict = []

    def export(self, data: dict, export_type: str) -> None:
        """Export data to JSON and log the information.

        Args:
            data: The data to export
            export_type: Type identifier (used as filename and for preset description)

        Returns:
            Tuple of (json_path, checksum) from the export operation
        """
        # Get description from presets or use custom if provided
        description = self.DESCRIPTIONS.get(
            export_type, f'Export of {export_type}'
        )

        # Export the data
        json_path, checksum = orjson_export(data, export_type)

        # Log the export if tracking is enabled
        if self.tracking_dict is not None:
            self.tracking_dict.append({
                'type': description,
                'path': json_path,
                'checksum': checksum,
            })

    def get_tracking_data(self) -> list:
        """Get the current tracking dictionary"""
        return self.tracking_dict
