use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ArchiveFormat {
    Zip,
    Tar,
    TarGz,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DatabaseFormat {
    Sqlite,
    Json,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PortableFormat {
    Json,
    Csv,
    Markdown,
}

impl ArchiveFormat {
    pub fn extension(&self) -> &'static str {
        match self {
            ArchiveFormat::Zip => "zip",
            ArchiveFormat::Tar => "tar",
            ArchiveFormat::TarGz => "tar.gz",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            ArchiveFormat::Zip => "ZIP Archive",
            ArchiveFormat::Tar => "TAR Archive",
            ArchiveFormat::TarGz => "TAR.GZ Archive",
        }
    }
}

impl DatabaseFormat {
    pub fn extension(&self) -> &'static str {
        match self {
            DatabaseFormat::Sqlite => "db",
            DatabaseFormat::Json => "json",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            DatabaseFormat::Sqlite => "SQLite Database",
            DatabaseFormat::Json => "JSON Database",
        }
    }
}

impl PortableFormat {
    pub fn extension(&self) -> &'static str {
        match self {
            PortableFormat::Json => "json",
            PortableFormat::Csv => "csv",
            PortableFormat::Markdown => "md",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            PortableFormat::Json => "JSON Format",
            PortableFormat::Csv => "CSV Format",
            PortableFormat::Markdown => "Markdown Format",
        }
    }
}