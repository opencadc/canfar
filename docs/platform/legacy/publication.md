# Publications (DOIs) {#publications-dois}

## Purpose {#purpose}
The **CANFAR Data Publication Service (DPS)** links a paper to the **data package** used in the research. DPS provides storage and registers a **DOI** with **DataCite**; the DOI permanently resolves to your landing page and data directory.

## Access {#access}
- [CANFAR Science Portal](https://www.canfar.net/) → **Data Publication**
- [Data Publication Service](https://www.canfar.net/citation/)

## Account requirements {#account}
The first author needs a CADC account to access the DPS UI and, later, the user‑managed storage (VOSpace).

!!! abstract "What you'll learn"
    - Request a DOI
    - Upload the data package
    - (Optional) Provide referee access
    - Publish via DataCite
---

## DOI guide {#doi-guide}

### 1) Request a DOI {#request}
- A DOI is reserved for your package (e.g., [10.11570/20.0006](http://doi.org/10.11570/20.0006)).
- A [**Data Directory** (VOSpace)](https://www.canfar.net/storage/vault/list/AstroDataCitationDOI/CISTI.CANFAR/20.0006/data) is created and accessible via the Web UI or `vos` tools.
- A [**landing page**](https://www.canfar.net/citation/landing?doi=20.0006) is generated.

### 2) Upload the data package {#upload}
Choose a method based on size and file count:

- Few/small files → [Use the Web Storage UI](storage.md)
- Large or many files → [Use the `vos, vcp` CLI tools](storage.md/#vos-cli)

More details: [DOI Data Package](#data-package).

### 3) Refereeing {#refereeing}
On request, CADC can create a **read‑only** account for the editor/referee to access the data directory. The account is disabled after review.

### 4) Publish with DataCite {#publish}
From DPS, click **Publish** to mint the DOI with DataCite and **lock** the Data Directory. Later metadata changes (e.g., adding the publication DOI) require contacting [CANFAR support](mailto:support@canfar.net).

---

## Using the DPS {#using}

### Listing current DOIs {#list}
[DPS](https://www.canfar.net/citation/) shows your DOIs (status, title, landing page, data directory). From here, you can request, view, edit, or publish depending on status.

### Requesting a new DOI {#new}
Use **New** from the list or go to the [request page](https://www.canfar.net/citation/request).

!!! question "Required"
    - First Author
    - Title

!!! note "Optional (can be edited later)"
    - Journal reference (journal, volume, page)
    - Additional Authors

After submission, a **DOI Reference** number is assigned and displayed.

### DOI Details {#details}
On the details page (e.g., [DOI.20.0016](https://www.canfar.net/citation/request?doi=20.0016)) you’ll find:

- DOI number / Title
- Authors / Journal reference
- DOI status
- Landing page link
- Data Directory link (shows :lock: when frozen)

### Editing details {#edit}
- **Unpublished** DOIs can be edited by authenticated users; click **Update**.
- **Published** DOIs require a request to [CANFAR support](mailto:support@canfar.net).

### Viewing the landing page {#landing}
- DOI: [10.11570/20.0016](http://doi.org/10.11570/20.0016)
- Landing page: [landing page](https://www.canfar.net/citation/landing?doi=20.0016)

Published landing pages are publicly accessible.

### Publishing a DOI {#publish-action}
If not yet published, a **Publish** button appears at the top right. Publishing:
- Completes registration with DataCite
- Locks the Data Directory

Related publication info can be added later via support.

### Deleting unpublished DOIs {#delete}
Unpublished records can be deleted via **Delete** on the request page. **Published** DOIs cannot be deleted.

---

## [DOI Data Package](#data-package) {#data-package}
DPS hosts a Data Directory in the **Vault (VOSpace)** implementation for each DOI. A folder named `data/` is created under the DOI root; you control the structure beneath it.

Example: [Data Directory](https://www.canfar.net/storage/vault/list/AstroDataCitationDOI/CISTI.CANFAR/21.0002/data)

!!! warning "Locked after publish"
    After publishing, the directory is **locked**. To modify contents or metadata, contact [CANFAR support](mailto:support@canfar.net).

### Contents {#contents}
You decide what to include: data, figures, software, etc. We recommend a top‑level `README` describing layout and usage.

### Uploading {#uploading}
- Few/small files: [Web Storage UI](storage.md).
- Large/many files: [Use `vcp`, `vos` CLI Tools](./storage.md#vos-cli).

### Refereeing access {#ref-access}
Contact support to obtain a read‑only account and share with the editor/referee. They may request changes prior to publication.

### Publish & discoverability {#discover}
After acceptance, click **Publish** to mint the DOI. The directory and metadata freeze; minimal discovery metadata will appear in DataCite search.

### Final linking {#final-link}
Finally, link the **data package DOI** to the **journal DOI** (currently manual):
- Email support with the publication DOI and updated reference details.
- Provide the data package DOI to the journal so it appears in the paper.