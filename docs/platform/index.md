# Official CANFAR Science Platform Documentation

## Introduction and Access

Access to the CANFAR Science Platform is through authorized access to the [CANFAR Portal](https://www.canfar.net). A Canadian Astronomy Data Centre (CADC) Account is required.

* To request a CADC Account:  https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html
* Authorization to access the science platform:
  * if you are part of a collaboration already using CANFAR, ask the admininistrator of the collaboration you belong to add you as a member of the group using the [Group Interface](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/)
  * in any other case, send an email to [support@canfar.net](mailto:support@canfar.net) specifying you are requesting access to the CANFAR Science Platform and a short line of justification.

The CANFAR Science Platform runs software packaged in [containers](https://www.docker.com/resources/what-container/). The platform allows users to run both pre-built, shared containers or private, custom containers. Users can publish container images to the [CANFAR Container Images Registry](https://images.canfar.net).  We have specific documentation on how to [build and publish](containers.md) capable to run on the CANFAR Science Platform.

The CANFAR Science Platform supports both launching interactive sessions and non-interactive ones. A more visual documentation for new users can be found [here](https://canfar-scienceportal.readthedocs.io/en/latest/). 

## Interactive Sessions

Interactive sessions are applications running server-side on the browser allowing users to interact with the (typically large) datasets hosted on CANFAR storage. There are a few types of Interactive Sessions on the platform:

### Notebooks
Notebooks are using the Jupyter Lab interface.

### CARTA 
[CARTA](https://cartavis.org/) (Cube Analysis and Rendering Tool for Astronomy) is an astronomy visualization tool that will run natively in the browser. It can read FITS or HDF5 files, often used in radio astronomy, but not only.

### Desktop

For running non browser-native applications in the Science Platform, a browser Desktop session can be launched.
- Desktop documentation and tutorials are described more in details in the [User Documentation](https://canfar-scienceportal.readthedocs.io/en/latest/NewUser/LaunchDesktop.html)
- Launching a CASA window in the Desktop YouTube tutorial:  [YouTube Tutorial](https://youtu.be/GDDQ3jKbldU)

### Contributed

Contributed sessions are user-customised web applications, typically not maintained by CANFAR. This can be anything, such as a [VSCode server](https://github.com/coder/code-server) and [Pluto notebook](https://plutojl.org/) for the Julia language. 

Please refer to the [container documentation](containers.md) for more information on building contributed sessions.

## Batch Jobs

There is limited possibility to run a batch job, which can be understood of a non-interactive executable launched on a headless container. Please contact us before making use of the headless job support--we are incrementally adding support for batch processing in the science platform. See the specific [documentation](headless.md). This is still experimental.

## Storage

All sessions and applications accessed through Science Platform can share the same filesystem mounted at `/arc`. Within are `/arc/home` (contains all home directories) and `/arc/projects` (for project use).  We encourage the use of `/arc/projects` for most data, and `/arc/home` for personalized configuration and software.

An efficient way to access the `arc` storage outside the Science Platform is through `sshfs`. Here is the [documentation](https://canfar-scienceportal.readthedocs.io/en/latest/General_tools/Using_sshfs.html).

The `arc` storage is also accesible through an API. The following list the ways it can be accessed beyond the use of the Science Portal and sshfs:

- Using the CANFAR storage management interface: https://www.canfar.net/storage/arc/list
- Using the [VOSpace Python libraries](https://github.com/opencadc/vostools/tree/master/vos)
- Using the `/arc/files` URL endpoint [documentation](https://ws-uv.canfar.net/arc)
- Using sshfs

More detailed instructions of the data transfer options are documented [here](https://canfar-scienceportal.readthedocs.io/en/latest/General_tools/File_transfers.html)

Please take care to protect sensitive information by ensuring it is not publicly accessible.

## Groups and Permissions

Projects are encouraged to use groups to manage access to resources, including files and directories in `arc` project storage, mounted at `/arc/projects` in every session.

Groups and their memberships can be managed through the CANFAR groups web interface, here: https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/

Once created, groups can be assigned to files and directories in arc storage directly from their interactive sessions, or through the [CANFAR storage](https://www.canfar.net/storage/arc/list)

For more details, see the documentation on [file permissions](permissions.md)

## Programmatic Access

Session launching and management is through the `skaha` service. The `skaha` API definition and science platform service are here:  https://ws-uv.canfar.net/skaha

## Community and Support

Dicussions of issues and platform features take place in the Science Platform Slack Channel: [Science Platform Slack Channel](https://cadc.slack.com/archives/C01K60U5Q87)

Reporting of bugs and new feature requests: 
- For the infrastructure and session https://github.com/opencadc/science-platform/issues
- For the containers: https://github.com/opencadc/science-containers/issues

Contributions to the platform (including updates or corrections to the documentation) can be submitted as pull requests to this GitHub repositories. We especially encourage science-containers.

General inquiries can be made to [support@canfar.net](mailto:support@canfar.net), and take a look at our [FAQ](faq.md).

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
