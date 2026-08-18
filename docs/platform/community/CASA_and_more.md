# CASA and adjacent astronomy software

CASA and related radio-astronomy tools are supplied through selected Container
Images. Availability and version-specific behavior belong to the image you
choose; check `canfar image ls` and the image documentation before writing a
workflow that depends on a package.

## Choose and inspect an image

```bash
canfar image ls --kind desktop
canfar create desktop IMAGE_NAME --name casa-work
```

Inside the running Session, check the installed CASA version and invoke the
command documented for that release. Keep the reduction script and measurement
sets under `/arc` or copy them from `/scratch` before the Session ends.

For package-specific usage, use the upstream documentation:

- [CASA documentation](https://casadocs.readthedocs.io/)
- [Astropy](https://docs.astropy.org/)
- [Astroquery](https://astroquery.readthedocs.io/)
- [Analysis Utilities](https://casaguides.nrao.edu/index.php/Analysis_Utilities)
- [UVMultiFit](https://github.com/onsala-space-observatory/UVMultiFit)
- [Galario](https://mtazzari.github.io/galario/)
- [Starlink](https://starlink.eao.hawaii.edu/starlink/)

If an application is missing or behaves differently from its upstream
documentation, record the Container Image name and version, the Session Kind,
the command, and the error before contacting [CANFAR support](../support/index.md).

For an end-to-end ALMA example, see the [ALMA analysis workflow](alma/index.md).
