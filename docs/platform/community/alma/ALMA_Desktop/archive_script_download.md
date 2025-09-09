# Using scripts to download ALMA archive data

How to download ALMA archive data in bulk using URL lists and command-line tools securely.

Use URL lists and command-line tools (wget, curl) or transfer tools for bulk downloads; ensure credentials are handled securely.

For large datasets obtain an URL list from the archive and use `wget` with the certificate you fetched with `cadc-get-cert`:

```sh
cadc-get-cert -u [username]
wget --content-disposition -i url_list.txt --certificate ~/.ssl/cadcproxy.pem --ca-certificate ~/.ssl/cadcproxy.pem
```

Alternatively use `vcp` to transfer directly into a VOSpace location.
