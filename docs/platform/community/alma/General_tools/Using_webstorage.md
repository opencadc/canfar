# Using web storage

Using the web UI to upload, download, and manage files in VOSpace or project storage; use URL lists for scripting.

## Upload File(s)

To upload one or more files (or folders), navigate to the desired directory, then click the `Add` button along the top, selecting the appropriate option. Follow the instructions on the pop-up box that appears to choose and upload your files.

## Download Files

Downloading files is also straightforward, and three options are outlined here: `URL List`, `HTML List`, and `Zip`. The `Zip` option will usually be the most practical, but the `HTML List` option may be preferred when downloading only a few files, and `URL List` may be best for scripting.

### Download - URL List Option

First, choose the `URL List` option, then select the desired directory and file name and click `save`.

If the file(s) is/are not publicly available, update your security certificates by running:

    cadc-get-cert -u [username]

Then download the files using `wget` with the provided URL list and certificates:

    wget --content-disposition -i cadcUrlList.txt --certificate ~/.ssl/cadcproxy.pem --ca-certificate ~/.ssl/cadcproxy.pem

### Download - HTML List Option

Clicking the `HTML List` option will bring up a pop up window with a series of long URL strings - each entry is a clickable direct link to your individual files.

### Download - Zip Option

The `Zip` option allows you to download a single zip file containing all of your requested files. Choose the `zip` option, and click `save` in the pop-up window after adjusting your preferred directory and zip file name.
