# File transfer overview

Summary of available file transfer methods: Notebook upload, web storage, VOS Tools, SSHFS, and direct URLs.

There are several ways to move files into and out of the Science Portal. Common options include:

- Notebook upload: small files can be uploaded via the Notebook file browser (see the Notebook transfer tutorial).
- Web storage: use the web interface to upload/download and manage files.
- VOS Tools: command-line tools (`vcp`, `vls`, `vrm`) for copying files to/from VOSpace and Science Portal locations.
- SSHFS: mount the remote file system locally and use rsync or other tools to sync files.
- Direct URL: obtain a direct ARC URL list and use `wget` with the appropriate certificate to download files.

See the individual tutorials for step-by-step instructions:

- Notebook uploads: /science-containers/general/Notebook/transfer_file
- Web storage: /science-containers/general/General_tools/Using_webstorage
- VOS Tools: /science-containers/general/General_tools/Using_vostools
- SSHFS: /science-containers/general/General_tools/Using_sshfs
- Direct URL downloads: /science-containers/general/TipsTricks/Direct_url
