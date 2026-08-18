# Publish data with a DOI

The CANFAR Data Publication Service (DPS) packages research data with a
landing page and a persistent Digital Object Identifier (DOI). Use the
[Science Portal](https://www.canfar.net/) or open the
[DPS](https://www.canfar.net/citation/) directly.

The service workflow is web-led. A CADC account and access to the data service
are required; if the portal does not show the publication tools, ask CANFAR
support about account or project access.

## Workflow

1. Open **Data Publication** and choose **New**.
2. Enter the required title and first-author details. Add authors and journal
   information when available.
3. Upload or copy the package into the data directory shown by DPS. For a
   command-line transfer, use the configured Storage Identifier and the
   [CANFAR data commands](storage/transfers.md):

   ```bash
   canfar data ls vault:/path/to/doi/data
   canfar data cp local:/scratch/catalog.csv vault:/path/to/doi/data/catalog.csv
   ```

   `vault:` is an example; use the identifier and path supplied by the
   publication service on your deployment.
4. Add a top-level `README` that describes the layout, provenance, software,
   units, and any restrictions. Include the data, code, figures, or tables
   needed to interpret the research, while excluding credentials and
   unnecessary temporary files.
5. Share the unpublished record or its data directory with referees using the
   access workflow provided by DPS.
6. Select **Publish** when the package and metadata are final. Publishing
   registers the DOI and locks the published data directory; contact
   [CANFAR support](mailto:support@canfar.net) if a published record needs a
   correction.

## Build a useful package

Keep the package self-describing and reproducible:

- record the source observations, processing steps, and software versions;
- use stable, descriptive filenames and a short directory structure;
- include machine-readable metadata alongside tables and images;
- document missing values, coordinate systems, units, and selection criteria;
- include a license and citation guidance for reuse; and
- verify that the package can be read from the published data directory before
  selecting **Publish**.

Use `/scratch` only for staging during a Session. Store the package and any
checkpoint that must survive outside `/arc` or the DPS data directory. The
[storage guide](storage/index.md) explains the distinction between mounted
storage, staged files, and persistent remote data.

## After publication

Use the DOI landing page in the paper and cite the dataset as a research
output. If the journal DOI or bibliographic details become available later,
update the unpublished metadata or contact support for the published record.

The DPS landing page and data-directory URLs are the source of truth for the
individual package. Do not hard-code a sample DOI or assume that a particular
Vault path is available to another user or deployment.

## Related guides

- [Data transfers](storage/transfers.md)
- [Storage and Python tools](storage/filesystem.md)
- [Permissions](permissions.md)
- [CANFAR support](support/index.md)
