"""A module to manage the creation of CSV files from metadata dictionaries."""

import csv
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urljoin

import jmespath
from dv_schema_models.dataset_instance import load_dataset
from loguru import logger

from dvmeta.models.config import Config
from dvmeta.models.csv_model import DatasetExportRow
from dvmeta.services.dir_manager import RES_DIR, ExportDir, get_dir
from dvmeta.services.timestamp import get_file_timestamp
from dvmeta.services.utils import (
    convert_size,
    gen_checksum,
    get_data_files_count,
    get_data_files_size,
)


class Spreadsheet:
    """A class to manage the creation of CSV files from metadata dictionaries."""

    def __init__(self, config: Config) -> None:
        """Initialize the class with the configuration settings."""
        self.config = config
        self.csv_file_dir = get_dir(ExportDir.CSV)
        self.spreadsheet_order_file_path = RES_DIR / "spreadsheet_order.csv"

    @staticmethod
    def serialize_row(row: DatasetExportRow) -> dict:
        """Serialize export row, joining lists into '; '-separated strings."""
        result = {}
        for key, value in row.items():
            if isinstance(value, list):
                result[key] = "; ".join(str(item) for item in value if item is not None)
            else:
                result[key] = value
        return result

    @staticmethod
    def _get_data_files_count(dictionary: dict) -> int | str:
        """Get data files count."""
        latest_version = dictionary.get("datasetVersion", {})
        if "files" in latest_version:
            return len(jmespath.search("datasetVersion.files", dictionary))
        return "Error"

    @staticmethod
    def _get_restricted_data_files_count(dictionary: dict) -> int | str:
        """Get restricted data files count."""
        latest_version = dictionary.get("datasetVersion", {})
        if "files" in latest_version:
            data_files_count: list = jmespath.search(
                "datasetVersion.files[?restricted==`true`]", dictionary
            )
            return len(data_files_count) if data_files_count else 0
        return "Error"

    @staticmethod
    def _get_datafile_meta_usage(dictionary: dict) -> dict:
        """Get datafile meta usage."""
        if dictionary.get("datasetVersion", {}).get("files"):
            file_nested_list = jmespath.search("datasetVersion.files[*]", dictionary)
            directorylabel_count = len([
                f for f in file_nested_list if f.get("directoryLabel") is not None
            ])
            categories_count = len([
                f for f in file_nested_list if f.get("dataFile", {}).get("categories") is not None
            ])
            description_count = len([
                f for f in file_nested_list if f.get("dataFile", {}).get("description") is not None
            ])
            return {
                "DF_Hierarchy": directorylabel_count,
                "DF_Tags": categories_count,
                "DF_Description": description_count,
            }
        return {"DF_Hierarchy": 0, "DF_Tags": 0, "DF_Description": 0}

    @staticmethod
    def _get_dataset_version(dataset_meta: dict) -> float | str:
        """Get dataset version."""
        dataset_version = dataset_meta.get("datasetVersion", {})
        if dataset_version.get("versionState") == "DRAFT":
            return "DRAFT"
        version_number = dataset_version.get("versionNumber")
        version_minor_number = dataset_version.get("versionMinorNumber")
        if version_number is not None and version_minor_number is not None:
            return float(f"{version_number}.{version_minor_number}")
        return "Error"

    @staticmethod
    def _get_dataset_subjects(subject_list: list) -> dict:
        """Get dataset subjects."""
        subject_map = {
            "CM_Subject_Agri": "Agricultural Sciences",
            "CM_Subject_AH": "Arts and Humanities",
            "CM_Subject_Astro": "Astronomy and Astrophysics",
            "CM_Subject_BM": "Business and Management",
            "CM_Subject_Chem": "Chemistry",
            "CM_Subject_Comp": "Computer and Information Science",
            "CM_Subject_EES": "Earth and Environmental Sciences",
            "CM_Subject_Eng": "Engineering",
            "CM_Subject_Law": "Law",
            "CM_Subject_Math": "Mathematical Sciences",
            "CM_Subject_Med": "Medicine, Health and Life Sciences",
            "CM_Subject_Phys": "Physics",
            "CM_Subject_SocSci": "Social Sciences",
            "CM_Subject_Other": "Other",
        }
        if subject_list:
            return {key: value in subject_list for key, value in subject_map.items()}
        return dict.fromkeys(subject_map, False)

    @staticmethod
    def _get_metadata_blocks_usage(dataset_meta: dict) -> dict:
        """Get metadata blocks usage."""
        metadata_block_map = {
            "Meta_Geo": "geospatial",
            "Meta_SSHM": "socialscience",
            "Meta_Astro": "astrophysics",
            "Meta_LS": "biomedical",
            "Meta_Journal": "journal",
            "Meta_CWF": "computationalworkflow",
        }
        metadata_blocks = dataset_meta.get("datasetVersion", {}).get("metadataBlocks", {})
        return {key: value in metadata_blocks for key, value in metadata_block_map.items()}

    @staticmethod
    def _parse_permission_values(dataset_meta: dict) -> dict:
        """Parse permission values."""
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
        """Get column order."""
        order_list = Path(self.spreadsheet_order_file_path).read_text(encoding="utf-8").splitlines()
        valid_columns = [col for col in order_list if col in row_keys]
        return valid_columns + [col for col in row_keys if col not in valid_columns]

    @staticmethod
    def get_dataset_path(ds_metadata: dict, dataset_title: str = "") -> str:
        """Get the dataset path from a nested isPartOf chain.

        Parameters
        ----------
            ds_metadata (dict): Dataset metadata containing the nested isPartOf chain.

        Returns
        -------
            str | None: The dataset path, or None if it cannot be built.
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

    def make_csv_file(self, meta_dict: dict) -> tuple[Path, str]:
        """Create a CSV file from the nested metadata list.

        Parameters
        ----------
        meta_dict : dict

        Returns
        -------
        tuple[Path, str]
        """
        csv_file_path = Path(self.csv_file_dir).joinpath(f"ds_metadata_{get_file_timestamp()}.csv")

        rows = []

        for dataset_meta in meta_dict.values():
            try:
                loaded_dataset = load_dataset(dataset_meta)
                logger.debug(
                    f"loaded dataset: {loaded_dataset.data.datasetVersion.datasetPersistentId}"
                )
            except Exception as e:
                logger.error(f"Failed to load dataset: {e}")
                continue

            file_stats = self._get_datafile_meta_usage(dataset_meta)

            citation_block = loaded_dataset.data.latestVersion.metadataBlocks.get("citation")
            if citation_block is None:
                logger.error(
                    f"Dataset {loaded_dataset.data.datasetVersion.datasetPersistentId} has no citation block, skipping"
                )
                continue
            subject_list: list = citation_block.get_value("subject") or []

            row: DatasetExportRow = {
                "DatasetTitle": citation_block.get_value("title") or "",
                "DatasetURL": (
                    urljoin(
                        self.config.base_url,
                        f"/dataset.xhtml?persistentId={loaded_dataset.data.datasetVersion.datasetPersistentId}",
                    )
                    if loaded_dataset.data.datasetVersion.datasetPersistentId
                    else ""
                ),
                "DS_Path": self.get_dataset_path(dataset_meta, citation_block.get_value("title")),
                "ID": loaded_dataset.data.id,
                "DatasetPersistentId": loaded_dataset.data.datasetVersion.datasetPersistentId,
                "DatasetId": loaded_dataset.data.datasetVersion.datasetId,
                "VersionState": loaded_dataset.data.datasetVersion.versionState,
                "LastUpdateTime": loaded_dataset.data.datasetVersion.lastUpdateTime,
                "ReleaseTime": loaded_dataset.data.datasetVersion.releaseTime,
                "CreateTime": loaded_dataset.data.datasetVersion.createTime,
                "Version": str(self._get_dataset_version(dataset_meta)),
                "FileCount": get_data_files_count(dataset_meta),
                "FileSize": get_data_files_size(dataset_meta),
                "FileSize_normalized": convert_size(get_data_files_size(dataset_meta)),
                "License": license_info.get("name")
                if (license_info := getattr(loaded_dataset.data.datasetVersion, "license", None))
                else "",
                "RestrictedFiles": self._get_restricted_data_files_count(dataset_meta),
                "TermsOfUse": loaded_dataset.data.datasetVersion.termsOfUse or "",
                "RequestAccess": loaded_dataset.data.datasetVersion.fileAccessRequest,
                "TermsAccess": loaded_dataset.data.datasetVersion.termsOfAccess or "",
                "DF_Hierarchy": file_stats["DF_Hierarchy"],
                "DF_Tags": file_stats["DF_Tags"],
                "DF_Description": file_stats["DF_Description"],
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
                "CM_Subject": subject_list,
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
                # Metadata blocks presence
                **self._get_metadata_blocks_usage(dataset_meta),
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
            f"Exported Dataset Metadata CSV: {csv_file_path}\nChecksum (SHA-256): {checksum}"
        )

        return csv_file_path, checksum
