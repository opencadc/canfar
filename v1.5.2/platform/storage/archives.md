# CADC archive data

The Canadian Astronomy Data Centre (CADC) archives hold observations from
telescopes such as CFHT, JCMT, and Gemini. Archive files are addressed by
an archive identifier, such as `cadc:CFHT/806045o.fits.fz`. They are not
VOSpace paths, so `canfar data` and your Storage Identifiers do not reach
them; use the CADC archive tools described here.

## Workflow

1. Find the observations in the [CADC search pages](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/)
   or with a TAP query, and note their identifiers.
2. Download into your project directory, `/arc/projects/PROJECT/`, so the
   files outlive the Session and your collaborators can read them. Keep large
   downloads out of your personal home.
3. Stage what one job needs into `/scratch`, process it there, and copy the
   results back to `/arc`.

## Install the tools

```bash
pip install cadcdata cadctap
```

`cadcdata` provides `cadcget` and `cadcinfo`, and `cadctap` provides
`cadc-tap`. Both install `cadcutils`, which provides `cadc-get-cert`.

## Download a file

`cadcinfo` prints a file's size, type, and MD5 checksum without downloading it:

```bash
cadcinfo CFHT/806045o.fits.fz
```

`cadcget` downloads one identifier per call. The `cadc:` scheme is optional,
`-o` names the destination file or directory, and `--fhead` fetches only the
FITS headers:

```bash
cadcget -o /arc/projects/PROJECT/raw/ CFHT/806045o.fits.fz
cadcget --fhead CFHT/806045o.fits.fz
```

Request a cutout by adding it to the identifier, quoted so the shell leaves
the brackets alone:

```bash
cadcget -o /scratch/cutout.fits "CFHT/806045o.fits.fz?cutout=[1][10:120,20:30]"
```

For a list of identifiers, one per line in `identifiers.txt`:

```bash
while read -r identifier; do
  cadcget -o /arc/projects/PROJECT/raw/ "$identifier"
done < identifiers.txt
```

Compare each download with the size and checksum from `cadcinfo` before
processing.

## Proprietary data

`cadcget` and `cadcinfo` are anonymous unless you pass a credential. For data
still in its proprietary period, pass the certificate that `canfar login cadc`
saved:

```bash
cadcget --cert ~/.ssl/cadcproxy.pem -o /arc/projects/PROJECT/raw/ CFHT/806045o.fits.fz
```

Without the CANFAR client, `cadc-get-cert -u USERNAME` writes the same file.
Your CADC account must belong to a group with access to the data; see
[Permissions](../permissions.md).

## Query with TAP

`cadc-tap` runs Table Access Protocol (TAP) queries in the Astronomical Data
Query Language (ADQL). Name the service with `-s`; without it, the tool queries
the user-catalogue service `ivo://cadc.nrc.ca/youcat`. The observation metadata
(CAOM) service is `ivo://cadc.nrc.ca/argus`.

Read the schema before writing a query, so column names come from the service:

```bash
cadc-tap schema -s ivo://cadc.nrc.ca/argus
cadc-tap schema -s ivo://cadc.nrc.ca/argus caom2.Observation
```

Then query. `-f` selects `tsv` (the default), `csv`, or `VOTable`, `-o` writes
to a file, and `-m` caps the number of rows:

```bash
cadc-tap query -s ivo://cadc.nrc.ca/argus -f csv -o observations.csv -m 100 \
  "SELECT observationID, collection FROM caom2.Observation WHERE collection = 'CFHT'"
```

Queries run synchronously, with a two-minute default that `--timeout MINUTES`
changes. `cadc-tap` looks for a `~/.netrc` entry, then
`~/.ssl/cadcproxy.pem`, and otherwise queries anonymously; `-a` forces an
anonymous query.

## Use the Python API

```python
import os

from cadcdata import StorageInventoryClient
from cadcutils import net

certificate = os.path.join(os.environ["HOME"], ".ssl/cadcproxy.pem")
client = StorageInventoryClient(net.Subject(certificate=certificate))
print(client.cadcinfo("CFHT/806045o.fits.fz"))
client.cadcget("CFHT/806045o.fits.fz", dest="/arc/projects/PROJECT/raw/")
```

`StorageInventoryClient()` with no argument is anonymous. `dest` accepts a
file name, a directory, or a writable stream.

## Related guides

- [Data transfers](transfers.md)
- [Storage](index.md)
- [Permissions](../permissions.md)
