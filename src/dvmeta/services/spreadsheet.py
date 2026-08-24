"""A module to manage the creation of CSV files from metadata dictionaries."""

import csv
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urljoin

from dv_schema_models.dataset_instance import DatasetVersion, safe_load_dataset
from dv_schema_models.file_instance import FileInstance
from loguru import logger

from dvmeta.models.config import Config
from dvmeta.models.csv_model import DatasetExportRow, DatasetSubjects, MetadataBlocks
from dvmeta.services.dir_manager import RES_DIR, ExportDir, get_dir
from dvmeta.services.timestamp import get_file_timestamp
from dvmeta.services.utils import convert_size, gen_checksum


class Spreadsheet:
    """A class to manage the creation of CSV files from metadata dictionaries."""

    def __init__(self, config: Config) -> None:
        """Initialize the class with the configuration settings."""
        self.config = config
        self.csv_file_dir = get_dir(ExportDir.CSV)
        self.spreadsheet_order_file_path = RES_DIR / "spreadsheet_order.csv"

    @staticmethod
    def serialize_row(row: DatasetExportRow) -> dict:
        """Serialize export row, joining lists into '; '-separated strings.

        Args:
            row: The export row to serialize.

        Returns:
            dict: A dictionary representing the serialized row.
        """
        result = {}
        for key, value in row.items():
            if isinstance(value, list):
                result[key] = "; ".join(str(item) for item in value if item is not None)
            else:
                result[key] = value
        return result

    @staticmethod
    def _get_dataset_version(dataset_version: DatasetVersion) -> str:
        """Get dataset version.

        Args:
            dataset_version: The dataset version object.

        Returns:
            str: The dataset version as a string or "DRAFT" if the version state is draft.
        """
        if dataset_version.versionState == "DRAFT":
            return "DRAFT"
        if (
            dataset_version.versionNumber is not None
            and dataset_version.versionMinorNumber is not None
        ):
            return str(f"{dataset_version.versionNumber}.{dataset_version.versionMinorNumber}")
        return "Error"

    @staticmethod
    def _get_dataset_subjects(subject_list: list[str] | None) -> dict[str, bool]:
        """Get dataset subjects, with the mapped boolean values for each subject.

        Args:
            subject_list: Subjects associated with the dataset, or None if none are provided.

        Returns:
            dict[str, bool]: Mapping of each known subject to whether it is in `subject_list`.
        """
        subjects = dict.fromkeys(DatasetSubjects.__members__, False)

        if not subject_list:
            return subjects

        for subject in subject_list:
            if key := DatasetSubjects.from_value(subject):
                subjects[key] = True

        return subjects

    @staticmethod
    def _parse_permission_values(dataset_meta: dict) -> dict:
        """Parse permission values.

        Args:
            dataset_meta: The dataset metadata.

        Returns:
            dict: Role-assignment counts, or "NA" placeholders if permissions weren't fetched.
        """
        permission_info = dataset_meta.get("permissions", {})
        if permission_info.get("status") != "OK":
            return {
                "DS_Permission": False,
                "DS_Collab": "NA",
                "DS_Admin": "NA",
                "DS_Contrib": "NA",
                "DS_ContribPlus": "NA",
                "DS_Curator": "NA",
                "DS_FileDown": "NA",
                "DS_Member": "NA",
            }
        data = permission_info.get("data") or []
        return {
            "DS_Permission": True,
            "DS_Collab": len(data),
            "DS_Admin": len([p for p in data if p.get("_roleAlias") == "admin"]),
            "DS_Contrib": len([p for p in data if p.get("_roleAlias") == "contributor"]),
            "DS_ContribPlus": len([p for p in data if p.get("_roleAlias") == "fullContributor"]),
            "DS_Curator": len([p for p in data if p.get("_roleAlias") == "curator"]),
            "DS_FileDown": len([p for p in data if p.get("_roleAlias") == "fileDownloader"]),
            "DS_Member": len([p for p in data if p.get("_roleAlias") == "member"]),
        }

    def _get_column_order(self, row_keys: list[str]) -> list[str]:
        """Get column order.

        Args:
            row_keys: The keys present in a serialized row.

        Returns:
            list[str]: `row_keys` ordered per `spreadsheet_order.csv`, unlisted keys appended last.
        """
        if Path(self.spreadsheet_order_file_path).exists():
            order_list = (
                Path(self.spreadsheet_order_file_path).read_text(encoding="utf-8").splitlines()
            )
        else:
            logger.warning(
                f"Spreadsheet order file not found at {self.spreadsheet_order_file_path}. "
                "Using default column order."
            )
            order_list = list(DatasetExportRow.__annotations__.keys())

        valid_columns = [col for col in order_list if col in row_keys]
        return valid_columns + [col for col in row_keys if col not in valid_columns]

    @staticmethod
    def get_dataset_path(ds_metadata: dict, dataset_title: str = "") -> str | None:
        """Get the dataset path from a nested isPartOf chain.

        Args:
            ds_metadata: The dataset metadata.
            dataset_title: The title of the dataset, by default "".

        Returns:
            The "/"-joined collection path, or None if `ds_metadata` has no isPartOf chain.
        """
        current = ds_metadata.get("data", {}).get("isPartOf")
        if not isinstance(current, Mapping):
            return ""

        names: list[str] = []

        while isinstance(current, Mapping):
            display_name = current.get("displayName")
            if isinstance(display_name, str) and display_name:
                names.append(display_name)

            next_node = current.get("isPartOf")
            if not isinstance(next_node, Mapping):
                break

            current = next_node

        if not names:
            return None

        names.insert(0, dataset_title)
        return "/".join(reversed(names))

    def make_csv_file(self, meta_dict: dict, *, timestamp_enabled: bool = True) -> tuple[Path, str]:
        """Create a CSV file from the nested metadata list.

        Args:
            meta_dict: Dataset metadata keyed by dataset ID.
            timestamp_enabled: Whether to include a timestamp in the filename, by default True.

        Returns:
            A tuple of (CSV file path, SHA-256 checksum).
        """
        csv_file_name = (
            f"ds_metadata_{get_file_timestamp()}.csv" if timestamp_enabled else "ds_metadata.csv"
        )
        csv_file_path = Path(self.csv_file_dir / csv_file_name)

        rows = []

        for key, dataset_meta in meta_dict.items():
            loaded_dataset = safe_load_dataset(dataset_meta)
            if isinstance(loaded_dataset, str):
                logger.warning(
                    f"Error loading dataset {key}: {loaded_dataset}, skipping to write to CSV"
                )
                continue
            dataset_version = loaded_dataset.dataset_version
            if not dataset_version:
                logger.warning(
                    f"Dataset {loaded_dataset.data.id} has no content metadata (likely deaccessioned), skipping to write to CSV"
                )
                continue
            citation_block = dataset_version.metadataBlocks.get("citation")
            if citation_block is None:
                logger.warning(
                    f"Dataset {dataset_version.datasetId} has no citation block, skipping to write to CSV"
                )
                continue
            subject_list: list = citation_block.get_value("subject") or []
            files_list = dataset_version.files or []

            row: DatasetExportRow = {
                "DatasetTitle": citation_block.get_value("title") or "",
                "DatasetURL": (
                    urljoin(
                        self.config.base_url,
                        f"/dataset.xhtml?persistentId={dataset_version.datasetPersistentId}",
                    )
                    if dataset_version.datasetPersistentId
                    else ""
                ),
                "DS_Path": self.get_dataset_path(dataset_meta, citation_block.get_value("title")),
                "ID": dataset_version.datasetId,
                "DatasetPersistentId": dataset_version.datasetPersistentId,
                "DatasetId": dataset_version.datasetId,
                "VersionState": dataset_version.versionState,
                "LastUpdateTime": dataset_version.lastUpdateTime,
                "ReleaseTime": dataset_version.releaseTime,
                "CreateTime": dataset_version.createTime,
                "Version": self._get_dataset_version(dataset_version),
                "FileCount": len(files_list),
                "FileSize": FileInstance.sum_field(files_list, "filesize") or 0,
                "FileSize_normalized": convert_size(
                    FileInstance.sum_field(files_list, "filesize") or 0
                ),
                "License": license_info.get("name")
                if (license_info := getattr(dataset_version, "license", None))
                else "",
                "RestrictedFiles": FileInstance.list_field(files_list, "restricted").count(True),
                "TermsOfUse": dataset_version.termsOfUse or "",
                "RequestAccess": dataset_version.fileAccessRequest,
                "TermsAccess": dataset_version.termsOfAccess or "",
                "DF_Hierarchy": FileInstance.list_field(files_list, "directoryLabel") is not None,
                "DF_Tags": FileInstance.list_field(files_list, "dataFile.description") is not None,
                "DF_Description": FileInstance.list_field(files_list, "dataFile.categories")
                is not None,
                # Citation — simple/primitive fields
                "CM_Subtitle": citation_block.get_value("subtitle") or "",
                "CM_AltTitle": citation_block.get_value("alternativeTitle") or [],
                "CM_AltURL": citation_block.get_value("alternativeURL") or "",
                "CM_Notes": citation_block.get_value("notesText") or "",
                "CM_Lang": citation_block.get_value("language") or [],
                "CM_ProdDate": citation_block.get_value("productionDate") or "",
                "CM_ProdLocation": citation_block.get_value("productionPlace") or [],
                "CM_DisDate": citation_block.get_value("distributionDate") or "",
                "CM_Depositor": citation_block.get_value("depositor") or "",
                "CM_DepositDate": citation_block.get_value("dateOfDeposit") or "",
                "CM_DataType": citation_block.get_value("kindOfData") or [],
                "CM_RelMaterial": citation_block.get_value("relatedMaterial") or [],
                "CM_RelDatasets": citation_block.get_value("relatedDatasets") or [],
                "CM_OtherRef": citation_block.get_value("otherReferences") or [],
                "CM_DataSources": citation_block.get_value("dataSources") or [],
                "CM_OriginSources": citation_block.get_value("originOfSources") or "",
                "CM_CharSources": citation_block.get_value("characteristicOfSources") or "",
                "CM_DocSources": citation_block.get_value("accessToSources") or "",
                "Meta_Geo": dataset_version.metadataBlocks.get(str(MetadataBlocks.META_GEO))
                is not None,
                "Meta_SSHM": dataset_version.metadataBlocks.get(str(MetadataBlocks.META_SSHM))
                is not None,
                "Meta_Astro": dataset_version.metadataBlocks.get(str(MetadataBlocks.META_ASTRO))
                is not None,
                "Meta_LS": dataset_version.metadataBlocks.get(str(MetadataBlocks.META_LS))
                is not None,
                "Meta_Journal": dataset_version.metadataBlocks.get(str(MetadataBlocks.META_JOURNAL))
                is not None,
                "Meta_CWF": dataset_version.metadataBlocks.get(str(MetadataBlocks.META_CWF))
                is not None,
                # Citation — compound fields (extract specific child values)
                "CM_Agency": citation_block.get_subfield_values("otherId", "otherIdAgency"),
                "CM_ID": citation_block.get_subfield_values("otherId", "otherIdValue"),
                "CM_Author": citation_block.get_subfield_values("author", "authorName"),
                "CM_NumberAuthors": len(citation_block.get_subfield_values("author", "authorName")),
                "CM_AuthorAff": citation_block.get_subfield_values("author", "authorAffiliation"),
                "CM_AuthorIDType": citation_block.get_subfield_values(
                    "author", "authorIdentifierScheme"
                ),
                "CM_AuthorID": citation_block.get_subfield_values("author", "authorIdentifier"),
                "CM_ContactName": citation_block.get_subfield_values(
                    "datasetContact", "datasetContactName"
                ),
                "CM_ContactAff": citation_block.get_subfield_values(
                    "datasetContact", "datasetContactAffiliation"
                ),
                "CM_Descr": citation_block.get_subfield_values(
                    "dsDescription", "dsDescriptionValue"
                ),
                "CM_DescrDate": citation_block.get_subfield_values(
                    "dsDescription", "dsDescriptionDate"
                ),
                "CM_Subject": citation_block.get_value(type_name="subject"),
                **self._get_dataset_subjects(subject_list),
                "CM_Keyword": citation_block.get_subfield_values("keyword", "keywordValue"),
                "CM_KeywordVocab": citation_block.get_subfield_values(
                    "keyword", "keywordVocabulary"
                ),
                "CM_KeywordURI": citation_block.get_subfield_values(
                    "keyword", "keywordVocabularyURI"
                ),
                "CM_TopicTerm": citation_block.get_subfield_values(
                    "topicClassification", "topicClassValue"
                ),
                "CM_TopicVocab": citation_block.get_subfield_values(
                    "topicClassification", "topicClassVocab"
                ),
                "CM_TopicURL": citation_block.get_subfield_values(
                    "topicClassification", "topicClassVocabURI"
                ),
                "CM_PubCit": citation_block.get_subfield_values(
                    "publication", "publicationCitation"
                ),
                "CM_PubIDType": citation_block.get_subfield_values(
                    "publication", "publicationIDType"
                ),
                "CM_PubID": citation_block.get_subfield_values(
                    "publication", "publicationIDNumber"
                ),
                "CM_PubURL": citation_block.get_subfield_values("publication", "publicationURL"),
                "CM_ProdName": citation_block.get_subfield_values("producer", "producerName"),
                "CM_ProdAff": citation_block.get_subfield_values("producer", "producerAffiliation"),
                "CM_ProdAbbrev": citation_block.get_subfield_values(
                    "producer", "producerAbbreviation"
                ),
                "CM_ProdURL": citation_block.get_subfield_values("producer", "producerURL"),
                "CM_ProdLogo": citation_block.get_subfield_values("producer", "producerLogoURL"),
                "CM_ContribName": citation_block.get_subfield_values(
                    "contributor", "contributorName"
                ),
                "CM_ContribType": citation_block.get_subfield_values(
                    "contributor", "contributorType"
                ),
                "CM_FundingAgency": citation_block.get_subfield_values(
                    "grantNumber", "grantNumberAgency"
                ),
                "CM_FundingID": citation_block.get_subfield_values(
                    "grantNumber", "grantNumberValue"
                ),
                "CM_DisName": citation_block.get_subfield_values("distributor", "distributorName"),
                "CM_DisAff": citation_block.get_subfield_values(
                    "distributor", "distributorAffiliation"
                ),
                "CM_DisAbbrev": citation_block.get_subfield_values(
                    "distributor", "distributorAbbreviation"
                ),
                "CM_DisURL": citation_block.get_subfield_values("distributor", "distributorURL"),
                "CM_DisLogoURL": citation_block.get_subfield_values(
                    "distributor", "distributorLogoURL"
                ),
                "CM_TimeStart": citation_block.get_subfield_values(
                    "timePeriodCovered", "timePeriodCoveredStart"
                ),
                "CM_TimeEnd": citation_block.get_subfield_values(
                    "timePeriodCovered", "timePeriodCoveredEnd"
                ),
                "CM_CollectionStart": citation_block.get_subfield_values(
                    "dateOfCollection", "dateOfCollectionStart"
                ),
                "CM_CollectionEnd": citation_block.get_subfield_values(
                    "dateOfCollection", "dateOfCollectionEnd"
                ),
                "CM_SeriesName": citation_block.get_subfield_values("series", "seriesName"),
                "CM_SeriesInfo": citation_block.get_subfield_values("series", "seriesInformation"),
                "CM_SoftwareName": citation_block.get_subfield_values("software", "softwareName"),
                "CM_SoftwareVers": citation_block.get_subfield_values(
                    "software", "softwareVersion"
                ),
                # Permission role counts
                **self._parse_permission_values(dataset_meta),
            }

            rows.append(self.serialize_row(row))

        fieldnames = self._get_column_order(list(rows[0].keys())) if rows else []
        with csv_file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        checksum = gen_checksum(csv_file_path)
        logger.info(
            f"Exported Dataset Metadata CSV: {csv_file_path}. Checksum (SHA-256): {checksum}"
        )

        return csv_file_path, checksum
