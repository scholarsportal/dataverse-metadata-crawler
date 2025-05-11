# ruff: noqa: PLR1733
"""A module to manage the creation of CSV files from metadata dictionaries."""
from pathlib import Path

import jmespath
import pandas as pd
from custom_logging import CustomLogger
from dirmanager import DirManager
from timestamp import Timestamp
from utils import convert_size
from utils import gen_checksum
from utils import list_to_string


# Initialize the logger
logger = CustomLogger().get_logger(__name__)


class Spreadsheet:
    """A class to manage the creation of CSV files from metadata dictionaries."""

    def __init__(self, config: dict) -> None:
        """Initialize the class with the configuration settings."""
        self.config = config
        self.search_string = """{
            DatasetTitle: data.metadataBlocks.citation.fields[?typeName==`title`].value|[]
            DS_Path: path_info.path
            DatasetPersistentId: data.datasetPersistentId,
            ID: data.id,
            DatasetId: data.datasetId,
            VersionState: data.versionState,
            LastUpdateTime: data.lastUpdateTime,
            ReleaseTime: data.releaseTime,
            CreateTime: data.createTime,
            License: data.license.name
            TermsOfUse: data.termsOfUse
            RequestAccess: data.fileAccessRequest
            TermsAccess: data.termsOfAccess
            versionNumber: data.versionNumber,
            versionMinorNumber: data.versionMinorNumber,
            CM_Subtitle: data.metadataBlocks.citation.fields[?typeName==`subtitle`].value|[]
            CM_AltTitle: data.metadataBlocks.citation.fields[?typeName==`alternativeTitle`].value|[]
            CM_AltURL: data.metadataBlocks.citation.fields[?typeName==`alternativeURL`].value|[]
            CM_Agency: data.metadataBlocks.citation.fields[?typeName==`otherId`].value|[*]|[].otherIdAgency.value
            CM_ID: data.metadataBlocks.citation.fields[?typeName==`otherId`].value|[*]|[].otherIdValue.value
            CM_Author: data.metadataBlocks.citation.fields[?typeName==`author`].value|[*]|[].authorName.value
            CM_AuthorAff: data.metadataBlocks.citation.fields[?typeName==`author`].value|[*]|[].authorAffiliation.value
            CM_AuthorID: data.metadataBlocks.citation.fields[?typeName==`author`].value|[*]|[].authorIdentifier.value
            CM_AuthorIDType: data.metadataBlocks.citation.fields[?typeName==`author`].value|[*]|[].authorIdentifierScheme.value
            CM_ContactName: data.metadataBlocks.citation.fields[?typeName==`datasetContact`].value|[*]|[].datasetContactName.value
            CM_ContactAff: data.metadataBlocks.citation.fields[?typeName==`datasetContact`].value|[*]|[].datasetContactAffiliation.value
            CM_Descr: data.metadataBlocks.citation.fields[?typeName==`dsDescription`].value|[*]|[].dsDescriptionValue.value
            CM_DescrDate: data.metadataBlocks.citation.fields[?typeName==`dsDescription`].value|[*]|[].dsDescriptionDate.value
            CM_Subject: data.metadataBlocks.citation.fields[?typeName==`subject`].value|[]
            CM_Keyword: data.metadataBlocks.citation.fields[?typeName==`keyword`].value|[].keywordValue.value
            CM_KeywordVocab: data.metadataBlocks.citation.fields[?typeName==`keyword`].value|[].keywordVocabulary.value
            CM_KeywordURI: data.metadataBlocks.citation.fields[?typeName==`keyword`].value|[].keywordVocabularyURI.value
            CM_TopicTerm: data.metadataBlocks.citation.fields[?typeName==`topicClassification`].value|[].topicClassValue.value
            CM_TopicVocab: data.metadataBlocks.citation.fields[?typeName==`topicClassification`].value|[].topicClassVocab.value
            CM_TopicURL: data.metadataBlocks.citation.fields[?typeName==`topicClassification`].value|[].topicClassVocabURI.value
            CM_PubCit: data.metadataBlocks.citation.fields[?typeName==`publication`].value|[].publicationCitation.value
            CM_PubIDType: data.metadataBlocks.citation.fields[?typeName==`publication`].value|[].publicationIDType.value
            CM_PubID: data.metadataBlocks.citation.fields[?typeName==`publication`].value|[].publicationIDNumber.value
            CM_PubURL: data.metadataBlocks.citation.fields[?typeName==`publication`].value|[].publicationURL.value
            CM_Notes: data.metadataBlocks.citation.fields[?typeName==`notesText`].value|[]
            CM_Lang: data.metadataBlocks.citation.fields[?typeName==`language`].value|[]
            CM_ProdName: data.metadataBlocks.citation.fields[?typeName==`producer`].value|[].producerName.value
            CM_ProdAff: data.metadataBlocks.citation.fields[?typeName==`producer`].value|[].producerAffiliation.value
            CM_ProdAbbrev: data.metadataBlocks.citation.fields[?typeName==`producer`].value|[].producerAbbreviation.value
            CM_ProdURL: data.metadataBlocks.citation.fields[?typeName==`producer`].value|[].producerURL.value
            CM_ProdLogo: data.metadataBlocks.citation.fields[?typeName==`producer`].value|[].producerLogoURL.value
            CM_ProdDate: data.metadataBlocks.citation.fields[?typeName==`productionDate`].value|[]
            CM_ProdLocation: data.metadataBlocks.citation.fields[?typeName==`productionPlace`].value|[]
            CM_ContribName: data.metadataBlocks.citation.fields[?typeName==`contributor`].value|[].contributorName.value
            CM_ContribType: data.metadataBlocks.citation.fields[?typeName==`contributor`].value|[].contributorType.value
            CM_FundingAgency: data.metadataBlocks.citation.fields[?typeName==`grantNumber`].value|[].grantNumberAgency.value
            CM_FundingID: data.metadataBlocks.citation.fields[?typeName==`grantNumber`].value|[].grantNumberValue.value
            CM_DisName: data.metadataBlocks.citation.fields[?typeName==`distributor`].value|[].distributorName.value
            CM_DisAff: data.metadataBlocks.citation.fields[?typeName==`distributor`].value|[].distributorAffiliation.value
            CM_DisAbbrev: data.metadataBlocks.citation.fields[?typeName==`distributor`].value|[].distributorAbbreviation.value
            CM_DisURL: data.metadataBlocks.citation.fields[?typeName==`distributor`].value|[].distributorURL.value
            CM_DisLogoURL: data.metadataBlocks.citation.fields[?typeName==`distributor`].value|[].distributorLogoURL.value
            CM_DisDate: data.metadataBlocks.citation.fields[?typeName==`distributionDate`].value|[]
            CM_Depositor: data.metadataBlocks.citation.fields[?typeName==`depositor`].value|[]
            CM_DepositDate: data.metadataBlocks.citation.fields[?typeName==`dateOfDeposit`].value|[]
            CM_TimeStart: data.metadataBlocks.citation.fields[?typeName==`timePeriodCovered`].value|[].timePeriodCoveredStart.value
            CM_TimeEnd: data.metadataBlocks.citation.fields[?typeName==`timePeriodCovered`].value|[].timePeriodCoveredEnd.value
            CM_CollectionStart: data.metadataBlocks.citation.fields[?typeName==`dateOfCollection`].value|[].dateOfCollectionStart.value
            CM_CollectionEnd: data.metadataBlocks.citation.fields[?typeName==`dateOfCollection`].value|[].dateOfCollectionEnd.value
            CM_DataType: data.metadataBlocks.citation.fields[?typeName==`kindOfData`].value|[]
            CM_SeriesName: data.metadataBlocks.citation.fields[?typeName==`series`].value|[].seriesName.value
            CM_SeriesInfo: data.metadataBlocks.citation.fields[?typeName==`series`].value|[].seriesInformation.value
            CM_SoftwareName: data.metadataBlocks.citation.fields[?typeName==`software`].value|[].softwareName.value
            CM_SoftwareVers: data.metadataBlocks.citation.fields[?typeName==`software`].value|[].softwareVersion.value
            CM_RelMaterial: data.metadataBlocks.citation.fields[?typeName==`relatedMaterial`].value|[]
            CM_RelDatasets: data.metadataBlocks.citation.fields[?typeName==`relatedDatasets`].value|[]
            CM_OtherRef: data.metadataBlocks.citation.fields[?typeName==`otherReferences`].value|[]
            CM_DataSources: data.metadataBlocks.citation.fields[?typeName==`dataSources`].value|[]
            CM_OriginSources: data.metadataBlocks.citation.fields[?typeName==`originOfSources`].value|[]
            CM_CharSources: data.metadataBlocks.citation.fields[?typeName==`characteristicOfSources`].value|[]
            CM_DocSources: data.metadataBlocks.citation.fields[?typeName==`accessToSources`].value|[]
            DS_Permission: permission_info.data
            DS_Collab: length(permission_info.data)
            DS_Admin: length(permission_info.data[?_roleAlias=='admin'])
            DS_Contrib: length(permission_info.data[?_roleAlias=='contributor'])
            DS_ContribPlus: length(permission_info.data[?_roleAlias=='fullContributor'])
            DS_Curator: length(permission_info.data[?_roleAlias=='curator'])
            DS_FileDown: length(permission_info.data[?_roleAlias=='fileDownloader'])
            DS_Member: length(permission_info.data[?_roleAlias=='member'])
            }"""  # noqa: E501
        self.csv_file_dir = DirManager().csv_files_dir()
        self.spreadsheet_order_file_path = Path(DirManager().res_dir) / 'spreadsheet_order.csv'

    @staticmethod
    def _mk_csv_file_dir() -> str:
        csv_file_dir = r'./csv_files'
        if not Path(csv_file_dir).exists():
            Path.mkdir(Path(csv_file_dir))

        return csv_file_dir

    @staticmethod
    def _get_data_files_size(dictionary: dict) -> int | str:
        data = dictionary.get('data')
        if data is not None and 'files' in data:
            data_files_size_list: list = jmespath.search('data.files[*].dataFile.filesize|[]', dictionary)
            if data_files_size_list:
                return sum(data_files_size_list)
        return 'Error'

    @staticmethod
    def _get_data_files_count(dictionary: dict) -> int | str:
        data = dictionary.get('data')
        if data is not None and 'files' in data:
            data_files_count: int = len(jmespath.search('data.files', dictionary))
            return data_files_count
        return 'Error'

    @staticmethod
    def _get_restricted_data_files_count(dictionary: dict) -> int | str:
        data = dictionary.get('data')
        if data is not None and 'files' in data:
            data_files_count: list = jmespath.search('data.files[?restricted==`true`]', dictionary)
            return len(data_files_count) if data_files_count else 0
        return 'Error'

    @staticmethod
    def _get_dataset_path(dictionary: dict) -> str:
        path_info = dictionary.get('path_info')
        if path_info is not None and 'path' in path_info:
            return path_info.get('path')
        if path_info is None:
            return 'root'
        return 'Error'

    @staticmethod
    def _get_dataset_version(dictionary: dict) -> float | str:
        version_number = dictionary.get('versionNumber')
        version_minor_number = dictionary.get('versionMinorNumber')
        if version_number is not None and version_minor_number is not None:
            return float(f'{version_number}.{version_minor_number}')
        return 'Error'

    @staticmethod
    def _get_dataset_subjects(dictionary: dict) -> dict:
        subject_list = dictionary.get('CM_Subject')
        subject_dict = {
            'CM_Subject_Agri': 'Agricultural Sciences',
            'CM_Subject_AH': 'Arts and Humanities',
            'CM_Subject_Astro': 'Astronomy and Astrophysics',
            'CM_Subject_BM': 'Business and Management',
            'CM_Subject_Chem': 'Chemistry',
            'CM_Subject_Comp': 'Computer and Information Science',
            'CM_Subject_EES': 'Earth and Environmental Sciences',
            'CM_Subject_Eng': 'Engineering',
            'CM_Subject_Law': 'Law',
            'CM_Subject_Math': 'Mathematical Sciences',
            'CM_Subject_Med': 'Medicine, Health and Life Sciences',
            'CM_Subject_Phys': 'Physics',
            'CM_Subject_SocSci': 'Social Sciences',
            'CM_Subject_Other': 'Other'
        }
        # Initialize an empty dictionary to store the result
        result_dict = {}

        # Iterate through the keys in return_dict and check if the subject is in subject_list
        if subject_list:
            for key, value in subject_dict.items():
                result_dict[key] = value in subject_list

        # If there are no subjects in the list, return a dictionary with all values set to False
        if not subject_list:
            return dict.fromkeys(subject_dict, False)

        return result_dict

    @staticmethod
    def _get_metadata_blocks_usage(dictionary: dict) -> dict:
        metadata_block_dict = {
            'Meta_Geo': 'geospatial',
            'Meta_SSHM': 'socialscience',
            'Meta_Astro': 'astrophysics',
            'Meta_LS': 'biomedical',
            'Meta_Journal': 'journal',
            'Meta_CWF': 'computationalworkflow',
            }

        # Loop through the metadata blocks and check if they are in the dictionary
        result_dict = {}
        for key, value in metadata_block_dict.items():
            result_dict[key] = value in dictionary

        return result_dict

    @staticmethod
    def _get_datafile_meta_usage(dictionary: dict) -> dict:
        # Get the use of data file directoryLabel (DF_Hierarchy),
        # tags (categories; DF_Tags) & description (DF_Description).
        if dictionary.get('data', {}).get('files'):
            file_nested_list = jmespath.search('data.files[*]', dictionary)

            # Get the count of directoryLabel if it is not None
            directorylabel_count = len([file for file in file_nested_list if file.get('directoryLabel') is not None])

            # Get the count of categories if it is not None
            categories_count = len([
                file for file in file_nested_list
                if file.get('dataFile', {}).get('categories') is not None
            ])

            # Get the count of description if it is not None
            description_count = len([
                file for file in file_nested_list
                if file.get('dataFile', {}).get('description') is not None
            ])

            return {'DF_Hierarchy': directorylabel_count,
                    'DF_Tags': categories_count,
                    'DF_Description': description_count}
        return {'DF_Hierarchy': 0, 'DF_Tags': 0, 'DF_Description': 0}

    @staticmethod
    def _parse_permission_values(dictionary: dict) -> dict | None:
        """Parse the NA value to permission_info.data, if the value is not available."""
        if dictionary.get('permission_info', {}).get('status', {}) == 'NA':
            # If the status is NA, set the DS_Permission, DS_Collab, DS_Admin, DS_Contrib
            # DS_ContribPlus, DS_Curator, DS_FileDown, DS_Member to NA
            return {
                'DS_Permission': False,
                'DS_Collab': 'NA',
                'DS_Admin': 'NA',
                'DS_Contrib': 'NA',
                'DS_ContribPlus': 'NA',
                'DS_Curator': 'NA',
                'DS_FileDown': 'NA',
                'DS_Member': 'NA'
            }
        return {'DS_Permission': True}

    def _get_spreadsheet_order(self) -> list[str]:
        with Path(self.spreadsheet_order_file_path).open(encoding='utf-8') as file:
            return file.read().splitlines()

    def _reorder_df_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        order_list = self._get_spreadsheet_order()

        # Filter the preset column order to only include existing columns in the DataFrame
        valid_columns = [col for col in order_list if col in df.columns]

        # Get columns not in the preset order
        remaining_columns = [col for col in df.columns if col not in valid_columns]

        # Combine valid columns (from the preset) and the remaining columns
        final_column_order = valid_columns + remaining_columns

        return df[final_column_order]

    def _make_cm_meta_holding_list(self, meta_dict: dict) -> list[dict]:
        """Create a nested list of metadata dictionaries.

        Args:
            meta_dict (dict): Dataset metadata dictionary.

        Returns:
            list[dict]: List of metadata dictionaries (nested)
        """
        holding_list = []
        for key, _value in meta_dict.items():
            jmespath_dict: dict = jmespath.search(f'{self.search_string}', meta_dict[key])

            # Get the use of data file hierarchy (folders, DF_Hierarchy),
            # file tags (categories; DF_Tags) &  description (DF_Description)
            jmespath_dict.update(self._get_datafile_meta_usage(meta_dict[key]))

            # Get the file size and count
            jmespath_dict['FileSize'] = self._get_data_files_size(meta_dict[key])
            jmespath_dict['FileSize_normalized'] = convert_size(jmespath_dict['FileSize'])
            jmespath_dict['FileCount'] = self._get_data_files_count(meta_dict[key])

            # Get the number of restricted files
            jmespath_dict['RestrictedFiles'] = self._get_restricted_data_files_count(meta_dict[key])

            # Get the URL for the dataset
            jmespath_dict['DatasetURL'] = f"{self.config['BASE_URL']}/dataset.xhtml?persistentId={jmespath_dict['DatasetPersistentId']}"  # noqa: E501

            # Get the dataset version
            jmespath_dict['Version'] = self._get_dataset_version(jmespath_dict)

            # Get the number of authors
            jmespath_dict['CM_NumberAuthors'] = len(jmespath_dict['CM_Author']) if jmespath_dict['CM_Author'] else 0

            # Get the number of subjects add the the result dictionary
            jmespath_dict.update(self._get_dataset_subjects(jmespath_dict))

            # Get the metadata blocks and add them to the result dictionary
            jmespath_dict.update(self._get_metadata_blocks_usage(jmespath_dict))

            # Drop the versionNumber and versionMinorNumber keys from the dictionary
            jmespath_dict.pop('versionNumber', None)
            jmespath_dict.pop('versionMinorNumber', None)

            # Update the permission info if the status is NA
            jmespath_dict.update(self._parse_permission_values(meta_dict[key]) or {})

            # Last step: Turn the lists in the dictionary into strings
            jmespath_dict = {key: list_to_string(value) if isinstance(value, list) else value for key, value in jmespath_dict.items()}

            holding_list.append(jmespath_dict)

        return holding_list

    def make_csv_file(self, meta_dict: dict) -> tuple[str, str]:
        """Create a CSV file from the nested metadata list.

        Args:
            meta_dict (dict): Dataset metadata dictionary

        Returns:
            tuple[str, str]: Path to the CSV file, Checksum of the CSV file
        """
        # Create a DataFrame from the nested list

        cm_meta_holding_list = self._make_cm_meta_holding_list(meta_dict)

        df = pd.DataFrame(cm_meta_holding_list)

        # Reorder the columns in the DataFrame according to to the preset order (/res/spreadsheet_order.csv)
        df = self._reorder_df_columns(df)

        # Create the CSV file
        csv_file_path = f'{self.csv_file_dir}/ds_metadata_{Timestamp().get_file_timestamp()}.csv'

        df.to_csv(csv_file_path, index=False)

        # Generate a checksum for the CSV file
        checksum = gen_checksum(csv_file_path)

        logger.print(f'Exported Dataset Metadata CSV: {csv_file_path}'
              f'\nChecksum (SHA-256): {checksum}')

        return csv_file_path, checksum
