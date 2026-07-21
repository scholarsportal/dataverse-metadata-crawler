"""The column structure of the dataset metadata CSV export."""

from typing import TypedDict


class DatasetExportRow(TypedDict, total=False):
    """Dataset spreadsheet export row."""

    DatasetTitle: str
    DatasetURL: str
    DS_Path: str

    ID: int
    DatasetPersistentId: str
    DatasetId: int

    Version: str
    VersionState: str
    LastUpdateTime: str
    ReleaseTime: str | None
    CreateTime: str

    FileCount: int | str
    FileSize: int
    FileSize_normalized: float

    License: str

    RestrictedFiles: int

    TermsOfUse: str
    RequestAccess: bool
    TermsAccess: str

    DF_Hierarchy: bool
    DF_Tags: bool
    DF_Description: bool

    CM_Subtitle: str

    CM_AltTitle: list[str]
    CM_AltURL: str

    CM_Agency: list[str]
    CM_ID: list[str]

    CM_NumberAuthors: int

    CM_Author: list[str]
    CM_AuthorAff: list[str]
    CM_AuthorIDType: list[str]
    CM_AuthorID: list[str]

    CM_ContactName: list[str]
    CM_ContactAff: list[str]

    CM_Descr: list[str]
    CM_DescrDate: list[str]

    CM_Subject: list[str]

    CM_Subject_Agri: bool
    CM_Subject_AH: bool
    CM_Subject_Astro: bool
    CM_Subject_BM: bool
    CM_Subject_Chem: bool
    CM_Subject_Comp: bool
    CM_Subject_EES: bool
    CM_Subject_Eng: bool
    CM_Subject_Law: bool
    CM_Subject_Math: bool
    CM_Subject_Med: bool
    CM_Subject_Phys: bool
    CM_Subject_SocSci: bool
    CM_Subject_Other: bool

    CM_Keyword: list[str]
    CM_KeywordVocab: list[str]
    CM_KeywordURI: list[str]

    CM_TopicTerm: list[str]
    CM_TopicVocab: list[str]
    CM_TopicURL: list[str]

    CM_PubCit: list[str]
    CM_PubIDType: list[str]
    CM_PubID: list[str]
    CM_PubURL: list[str]

    CM_Notes: str

    CM_Lang: list[str]

    CM_ProdName: list[str]
    CM_ProdAff: list[str]
    CM_ProdAbbrev: list[str]
    CM_ProdURL: list[str]
    CM_ProdLogo: list[str]

    CM_ProdDate: str
    CM_ProdLocation: list[str]

    CM_ContribType: list[str]
    CM_ContribName: list[str]

    CM_FundingAgency: list[str]
    CM_FundingID: list[str]

    CM_DisName: list[str]
    CM_DisAff: list[str]
    CM_DisAbbrev: list[str]
    CM_DisURL: list[str]
    CM_DisLogoURL: list[str]

    CM_DisDate: str

    CM_Depositor: str
    CM_DepositDate: str

    CM_TimeStart: list[str]
    CM_TimeEnd: list[str]

    CM_CollectionStart: list[str]
    CM_CollectionEnd: list[str]

    CM_DataType: list[str]

    CM_SeriesName: str
    CM_SeriesInfo: str

    CM_SoftwareName: list[str]
    CM_SoftwareVers: list[str]

    CM_RelMaterial: list[str]
    CM_RelDatasets: list[str]

    CM_OtherRef: list[str]
    CM_DataSources: list[str]

    CM_OriginSources: str
    CM_CharSources: str
    CM_DocSources: str

    Meta_Geo: bool
    Meta_SSHM: bool
    Meta_Astro: bool
    Meta_LS: bool
    Meta_Journal: bool
    Meta_CWF: bool

    DS_Permission: bool

    DS_Collab: int
    DS_Admin: int
    DS_Contrib: int
    DS_ContribPlus: int
    DS_Curator: int
    DS_FileDown: int
    DS_Member: int
