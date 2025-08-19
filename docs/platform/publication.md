# The CANFAR Data Publication Service

## Purpose
The purpose of the CANFAR Data Publication Service (DPS) is to support linking a research paper to the actual data that were used to produce the conclusions of that paper. The DPS provides storage space and the ability to register (publish) a Digital Object Identifier (DOI) with the DataCite system. That DOI will point to the published data on a permanent basis.

## Access
There are 2 ways to access the DPS:

- From the CANFAR portal (select Data Publication at <https://www.canfar.net/>)
- Through direct link - <https://www.canfar.net/citation/>

## Account Requirements
The author of the paper will need to have a CADC account. This will allow you to access the CANFAR Data Publication Service (DPS) interface and, later, to access the user-managed storage service where the author will deposit the data to be published.

---

## DOI Guide

!!! abstract "🎯 What You'll Learn"

    - Request a DOI
    - Upload the data package
    - Refereeing
    - Publish DOI with DataCite  

---

### 1. Request a DOI

  - A DOI number is reserved for the data package associated with the paper (e.g. `10.11570/20.0006`).

  - A Data Directory is created to house the data package. This is a VOSpace folder accessible via the User Storage UI or vos Python tools. [Check out this example.](https://www.canfar.net/storage/list/AstroDataCitationDOI/CISTI.CANFAR/20.0006/data)

  - A [landing page](https://www.canfar.net/citation/landing?doi=20.0006) is generated for the DOI.

### 2. Upload the data package

There are two ways to upload a data package. Which method you use depends on the size and complexity of the data being uploaded.

- For a smaller number of small-sized files, the User Storage UI is a good choice. Documentation: User Storage documentation

- For very large files, or for large numbers of files, the Python vcp tools are a better choice. Full instructions for using vcp can also be found under ‘The vos Python module and command line client’ in the User Storage documentation

For more details, see [DOI Data Package](#doi-data-package)

### 3. Refereeing
At the request of the DOI owner, a CADC account is generated with read-only access to the data package. The author can share it with a journal editor or referee. The account is disabled after refereeing is complete.

### 4. Publish DOI with DataCite
Through the CANFAR DPS, the DOI is “Published” with DataCite and the Data Directory is locked.  
Further changes to the data package or metadata (e.g. adding a Publication DOI) require a request to [CANFAR support](mailto:support@canfar.net).

---

## How to use the CANFAR Data Publication Service (DPS)

### Listing current DOIs
The list of CANFAR-hosted DOIs available to the authenticated user is shown at <https://www.canfar.net/citation/>.  
This page displays DOI details including status, name, title, landing page, and data directory links.  
From here, a DOI can be requested, viewed, edited, or published depending on status.

### Requesting a new DOI
From either the DOI list or request page, a 'New' button will be available. Click this to generate a new DOI request. The request form can be found at <https://www.canfar.net/citation/request>.

!!!question "Required Information"
    - First Author  
    - Title  

!!! note "Optional Information"
    - Journal reference (journal name, volume, page). This is typically not known initially.  
    - Additional Authors  
    - _Can be edited at a later stage_

Once the information is entered, push the 'Request' button. The DOI Reference number is assigned automatically and is displayed once the page refreshes.

### DOI Details

From the web interface, select the number or title to see more details on the DOI request page, e.g. [DOI.20.0016](https://www.canfar.net/citation/request?doi=20.0016) which includes,

  - DOI number  
  - Title  
  - First and Additional Authors  
  - Journal Reference  
  - DOI status  
  - Landing page link  
  - Data Directory link (:lock: if frozen)

### Editing DOI details
On the DOI request page, if a DOI is **NOT published**, details can be edited by an authenticated user.  
Modify any available values and press 'Update'. The new values are displayed when the page refreshes.  

If a DOI is published, a request to edit it must be made through CANFAR support.

### Viewing DOI landing page
The landing page provides public information about the journal paper and related data. It is the document DataCite links your DOI to.  

Example:  
- DOI: <http://doi.org/10.11570/20.0016>  
- Landing page: <https://www.canfar.net/citation/landing?doi=20.0016>  

The page contains information about the paper, links to the published data, and related publications.  
For DOIs that are published, the page is available anonymously.

### Publishing a DOI
On the DOI request page, if a DOI is **NOT already published**, there is a 'Publish' button in the upper right corner.  
When satisfied that all information is complete, press 'Publish'. The system will:  

- Complete registration of your DOI with DataCite  
- Lock the Data Directory  

Related publication info can be added later by contacting [CANFAR support](mailto:support@canfar.net).

### Deleting Unpublished DOIs
A DOI request can be deleted prior to publication using the 'Delete' action on the request page.  

**NOTE:** For published DOIs, no 'Delete' action is available.

## [DOI Data Package](#data-package)
DPS provides a Data Directory for the data package to reside in. The Data Directory is hosted by CANFAR in the Vault VOSpace impelmentation. A folder (literally called ‘data’) is created in the main folder for a DOI. The structure below that point is up to the DOI owner.

example: <https://www.canfar.net/storage/vault/list/AstroDataCitationDOI/CISTI.CANFAR/21.0002/data>

NOTE: after a DOI is published, this folder is locked and can no longer be modified without assistance from [CANFAR support](mailto:support@canfar.net).

### Content of the data package
The author has complete control of the content of the data package. It may contain data, figures, software, or any other material that is important to the paper. We recommend that a README file be placed at the top-level directory that explains the content (including the structure) of the data package.

### Uploading a data package
There are two ways to upload a data package. Which method you use depends on the size and complexity of the data being uploaded.

- For a smaller number of small-sized files, the User Storage UI is a good choice. Documentation: User Storage documentation

- For very large files, or for large numbers of files, the Python vcp tools are a better choice. Full instructions for using vcp can also be found under ‘The vos Python module and command line client’ in the User Storage documentation

### Refereeing: Sharing the data package with the journal editor and referee
Sharing the data package with the science community enhances and supplements the journal publication process. Furthermore, evaluation and assessment of the data package by the journal editors and referees is an additional enhancement to the value of data publication.

Authors should contact [CANFAR support](mailto:support@canfar.net) to obtain a user name and password for an account that can access (in readonly mode) the folder hosting the data package. The author can share this account information with the journal editor. The editor can then pass that account information on to the referee.

The referee and journal editor can examine the data package and may require revisions to the data prior to publication.

The journal editor and referee may examine and approve the revisions or modifications.

### Revising the Content of the data package
The author retains the ability to modify the data package and may do so at any point prior to publishing their DOI. After publication, the DOI owner needs to contact [CANFAR support](mailto:support@canfar.net) for assistance.

## Publishing (minting) the DOI
Once the refereeing process is complete and the paper is accepted the author can use the Publish button to “mint” (register the DOI with DataCite). This will lock the folder hosting the data package and the DOI information itself (author list, journal reference, etc.) so that the author can no longer make changes. The data will be discoverable through the DataCite search interface (with very limited discovery metadata).

## Revising and finalising publication and data package information
The final step is to link the data package DOI with the journal DOI. This is not currently automated.

The author should contact [CANFAR support](mailto:support@canfar.net) to:

- include the journal paper DOI in the data package information
- update the journal reference (title, volume, page)

It’s the responsibility of the author to provide the data package DOI to the journal editor to have it included in the journal paper.

## Need further assistance?
Please contact [CANFAR support](mailto:support@canfar.net) if you need any assistance.

Comments and feedback from users is greatly valued.
