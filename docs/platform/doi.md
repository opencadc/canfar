# Data Publication Service (DOIs)

CANFAR's Data Publication Service (DPS) provides permanent Digital Object Identifiers (DOIs) for research data packages, ensuring long-term accessibility and proper citation of datasets supporting astronomical publications.

!!! abstract "🎯 DOI Service Overview"
    **Essential data publication workflows:**
    
    - **DOI Registration**: Reserve permanent identifiers through DataCite
    - **Data Packaging**: Organise and upload research datasets
    - **Referee Access**: Provide controlled access during peer review
    - **Publication**: Mint final DOIs with locked data directories
    - **Long-term Preservation**: Ensure data accessibility and citation

## 🚀 Service Purpose & Access

### Data Publication Service Overview

The **CANFAR Data Publication Service (DPS)** creates permanent links between research papers and their supporting data packages. DPS provides:

- **Permanent Storage**: Reliable hosting for research data packages
- **DOI Registration**: Official Digital Object Identifiers through DataCite
- **Landing Pages**: Professional presentation of datasets and metadata
- **Citation Support**: Proper attribution for data reuse and collaboration

### Access Points

**Web Interface**
:   [CANFAR Science Portal](https://www.canfar.net/) → **Data Publication**

**Direct Service**
:   [Data Publication Service](https://www.canfar.net/citation/)

**Account Requirements**
:   First author requires a CADC account for DPS access and VOSpace data management.

## 📋 DOI Workflow Guide

### Step 1: Request a DOI

**Reserve Your DOI:**

- A permanent DOI is assigned to your data package (e.g., [10.11570/20.0006](http://doi.org/10.11570/20.0006))
- A dedicated [Data Directory (VOSpace)](https://www.canfar.net/storage/vault/list/AstroDataCitationDOI/CISTI.CANFAR/20.0006/data) is created
- A professional [landing page](https://www.canfar.net/citation/landing?doi=20.0006) is generated

### Step 2: Upload Data Package

**Choose Upload Method Based on Data Size:**

**Small/Few Files:**
:   Use the Web Storage UI for direct browser upload

**Large/Many Files:**
:   Use [`vos` CLI tools](storage/vospace.md) for efficient bulk transfer

See [Data Package Guidelines](#data-package-requirements) for content organization recommendations.

### Step 3: Referee Access (Optional)

**Peer Review Support:**

CADC can create read-only accounts for editors/referees to access your data directory during the review process. The temporary account is disabled after review completion.

### Step 4: Publish with DataCite

**Final Publication:**

Click **Publish** in the DPS interface to:

- Complete DOI registration with DataCite
- Lock the data directory (preventing further changes)
- Make the landing page publicly accessible

!!! warning "Important: Publication Locks Data"
    After publishing, the data directory becomes read-only. Metadata changes require contacting [CANFAR support](mailto:support@canfar.net).

## 🔧 Using the Data Publication Service

### Managing Your DOIs

**DOI Dashboard:**
:   The [DPS interface](https://www.canfar.net/citation/) displays all your DOIs with status, title, landing page links, and data directory access.

**Creating New DOIs:**
:   Use **New** from the dashboard or go directly to the [request page](https://www.canfar.net/citation/request).

### DOI Request Requirements

**Required Information:**

- **First Author**: Primary researcher responsible for the data package
- **Title**: Descriptive title for the dataset

**Optional Information (editable later):**

- **Additional Authors**: Contributing researchers
- **Journal Reference**: Journal name, volume, page numbers
- **Publication Details**: Can be added after manuscript acceptance

### DOI Management Interface

**DOI Details Page** (e.g., [DOI.20.0016](https://www.canfar.net/citation/request?doi=20.0016)):

- DOI reference number and dataset title
- Author list and journal reference information  
- Current publication status
- Direct links to landing page and data directory
- Lock status indicator for published DOIs

**Editing Capabilities:**

- **Unpublished DOIs**: Full editing access via **Update** button
- **Published DOIs**: Changes require [CANFAR support](mailto:support@canfar.net) request

**Landing Page Access:**

- **DOI Link**: [10.11570/20.0016](http://doi.org/10.11570/20.0016) (permanent identifier)
- **Landing Page**: [Direct access](https://www.canfar.net/citation/landing?doi=20.0016) (publicly accessible after publication)

**DOI Lifecycle Management:**

- **Unpublished**: Can be edited or deleted by the author
- **Published**: Permanent and locked, requires support for modifications

## 📦 Data Package Requirements

### Storage Implementation

**VOSpace Data Directory:**
:   Each DOI receives a dedicated folder in the CANFAR Vault (VOSpace) with a `data/` subdirectory under your control.

**Example Structure:**
:   [Data Directory Example](https://www.canfar.net/storage/vault/list/AstroDataCitationDOI/CISTI.CANFAR/21.0002/data)

### Content Organization

**Recommended Package Contents:**

- **Primary Data**: Core datasets supporting the research
- **Analysis Code**: Scripts and software used in data processing
- **Documentation**: README files describing structure and usage
- **Supplementary Materials**: Figures, tables, additional analysis outputs

**Best Practices:**

- Include a top-level README describing package layout and usage instructions
- Organize files in logical subdirectories (e.g., `raw_data/`, `processed/`, `scripts/`, `figures/`)
- Use descriptive filenames and provide metadata where appropriate

### Upload Methods

**Web Interface Upload:**
:   Web Storage UI for small datasets and simple uploads

**Command-Line Upload:**
:   `vcp` and `vos` CLI tools for large datasets and automated transfers

### Publication & Access Control

**Pre-Publication (Referee Access):**

- Contact [CANFAR support](mailto:support@canfar.net) for read-only reviewer accounts
- Temporary access provided during peer review process
- Reviewers may request changes before publication approval

**Post-Publication (Public Access):**

- **Publish** button mints the final DOI and locks data directory
- Landing page becomes publicly discoverable through DataCite search
- Minimal discovery metadata appears in DataCite registry

### Final Publication Integration

**Linking DOIs:**

After manuscript acceptance, coordinate the connection between your data package DOI and journal publication DOI:

1. **Notify Journal**: Provide your data package DOI for inclusion in the published paper
2. **Update Metadata**: Email [CANFAR support](mailto:support@canfar.net) with:
   - Publication DOI from the journal
   - Updated reference details (journal, volume, pages)
   - Any additional metadata corrections

!!! tip "Data Package Success"
    **Plan your data package early in the research process** to ensure all necessary files, documentation, and metadata are preserved and organized for publication.

## Using the DPS

### Listing current DOIs

[DPS](https://www.canfar.net/citation/) shows your DOIs (status, title, landing page, data directory). From here, you can request, view, edit, or publish depending on status.

### Requesting a new DOI

Use **New** from the list or go to the [request page](https://www.canfar.net/citation/request).

!!! question "Required"
    - First Author
    - Title

!!! note "Optional (can be edited later)"
    - Journal reference (journal, volume, page)
    - Additional Authors

After submission, a **DOI Reference** number is assigned and displayed.

### DOI Details

On the details page (e.g., [DOI.20.0016](https://www.canfar.net/citation/request?doi=20.0016)) you'll find:

- DOI number / Title
- Authors / Journal reference
- DOI status
- Landing page link
- Data Directory link (shows 🔒 when frozen)

### Editing details

- **Unpublished** DOIs can be edited by authenticated users; click **Update**.
- **Published** DOIs require a request to [CANFAR support](mailto:support@canfar.net).

### Viewing the landing page

- DOI: [10.11570/20.0016](http://doi.org/10.11570/20.0016)
- Landing page: [landing page](https://www.canfar.net/citation/landing?doi=20.0016)

Published landing pages are publicly accessible.

### Publishing a DOI

If not yet published, a **Publish** button appears at the top right. Publishing:

- Completes registration with DataCite
- Locks the Data Directory

Related publication info can be added later via support.

### Deleting unpublished DOIs

Unpublished records can be deleted via **Delete** on the request page. **Published** DOIs cannot be deleted.

## DOI Data Package

DPS hosts a Data Directory in the **Vault (VOSpace)** implementation for each DOI. A folder named `data/` is created under the DOI root; you control the structure beneath it.

Example: [Data Directory](https://www.canfar.net/storage/vault/list/AstroDataCitationDOI/CISTI.CANFAR/21.0002/data)

!!! warning "Locked after publish"
    After publishing, the directory is **locked**. To modify contents or metadata, contact [CANFAR support](mailto:support@canfar.net).

### Contents

You decide what to include: data, figures, software, etc. We recommend a top‑level `README` describing layout and usage.

### Uploading

- Few/small files: [Web Storage UI](storage/transfers.md#upload-methods).
- Large/many files: [Use `vcp`, `vos` CLI Tools](storage/transfers.md#large-files-100gb-advanced-methods).

### Refereeing access

Contact support to obtain a read‑only account and share with the editor/referee. They may request changes prior to publication.

### Publish & discoverability

After acceptance, click **Publish** to mint the DOI. The directory and metadata freeze; minimal discovery metadata will appear in DataCite search.

### Final linking

Finally, link the **data package DOI** to the **journal DOI** (currently manual):

- Email support with the publication DOI and updated reference details.
- Provide the data package DOI to the journal so it appears in the paper.