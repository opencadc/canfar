# Official CANFAR Science Platform Documentation

## Introduction and Access

The CANFAR Science Platform consists of set of services and resources to enable cloud-based astronomy data analysis.  Browser-based access to CANFAR's cloud computing layer is provided via authorized access to the [CANFAR Portal](https://www.canfar.net). A Canadian Astronomy Data Centre (CADC) account that has been authorized to use the Portal is required.

- To request a CADC Account:  https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html
- Authorization to access the CANFAR Portal:

    * If the project you are using the resource for is part of a collaboration already using the CANFAR Science Portal, ask the administrator of the collaboration you belong to add you as a member of the collaborations access group using the [CADC Group Management Interface](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/)
    * If your project is not part of an authorized collaboration, the collaboration lead will need to request access by sending an email to [support@canfar.net](mailto:support@canfar.net) specifying they are requesting access to the CANFAR Science Portal, the scale of resources needed (storage and cores of compute) and a short (few line) resource justification.  Canadian research collaborations are encouraged to apply for CANFAR Science Portal authorization.

The CANFAR Science Portal runs software packaged in [containers](https://www.docker.com/resources/what-container/). The portal allows users to run both pre-built, shared containers or private, custom containers. Authorized collaboration members can publish container images to the [CANFAR Container Images Registry](https://images.canfar.net).  We have specific documentation on how to [build and publish](containers.md) containers capable of being launched within the CANFAR Science Portal.

The CANFAR Science Platform supports both launching interactive sessions (via the Portal) and non-interactive ones (using cURL or a dedicated Python module). More detailed documentation on launching a computing session on the CANFAR Science Portal can be found [here](https://canfar-scienceportal.readthedocs.io/en/latest/). 

## Interactive Sessions

Interactive sessions are applications running on the CANFAR cloud infrastructure and are accessed via a web browser, allowing users to interact with the (typically large) datasets hosted on CANFAR Science Platform storage. There are a few types of Interactive Sessions that cab be launched through the portal:

### Notebooks
Notebooks are using the Jupyter Lab interface.

### CARTA 
[CARTA](https://cartavis.org/) (Cube Analysis and Rendering Tool for Astronomy) is an astronomy visualization tool that will run natively in the browser. It can read FITS or HDF5 files, often used in radio astronomy, but not only.

### Desktop

An X11-desktop session that enables running applications in the Science Platform, a browser Desktop session can be launched.
- 
- Desktop documentation and tutorials are described in more detail in the [User Documentation](https://canfar-scienceportal.readthedocs.io/en/latest/NewUser/LaunchDesktop.html)
- Launching a CASA window in the Desktop YouTube tutorial:  [YouTube Tutorial](https://youtu.be/GDDQ3jKbldU)

### Contributed

Contributed sessions are user-customised web applications, typically not maintained by CANFAR. This can be anything, such as a [VSCode server](https://github.com/coder/code-server) and [Pluto notebook](https://plutojl.org/) for the Julia language. 

Please refer to the [container documentation](containers.md) for more information on building contributed sessions.

## Batch Jobs

Currently, the CANFAR Science Platform has a limited capacity for batch processing.  Batch processing can be understood  as a non-interactive executable launched on a container whose output is not attached to a display (headless). Please contact [support@canfar.net](mailto:support@canfar.net) before making use of the headless job support -- we are incrementally adding support for batch processing in the science platform. See the specific [documentation](headless.md). This is still experimental and the API may change.

## Storage

All sessions and applications accessed through the Science Platform (interactive and batch) share a common storage system in the directory `/arc`. The primary folder/directories `/arc/home` and `/arc/projects`.  `/arc/home/${USERNAME}` contains a user's environment initializations details and personal information that might not be shared with collaboration members. `/arc/projects/${GROUP_NAME}` holds the data that the given group will be processing and the outputs of that processing. CANFAR encourages the use of `/arc/projects` for most data, and `/arc/home` for personalized configuration and software.  By default a user's `/arc/home/${USER}` folder is not readable by others on the platform.

An efficient and convenient way to access the `arc` storage outside the Science Platform is through `sshfs`. Here is the [documentation](https://canfar-scienceportal.readthedocs.io/en/latest/General_tools/Using_sshfs.html).

In addition to `sshfs` mentioned above, the `arc` storage is also accessible via an API that is exposed:

- Using the CANFAR storage management interface: https://www.canfar.net/storage/arc/list
- Using the [VOSpace Python libraries](https://github.com/opencadc/vostools/tree/master/vos)
- Using the `/arc/files` URL endpoint [documentation](https://ws-uv.canfar.net/arc)


More detailed instructions on data transfer options are documented here: [here](https://canfar-scienceportal.readthedocs.io/en/latest/General_tools/File_transfers.html)

Please take care to protect sensitive information by ensuring it is not publicly accessible.  File access control on `arc` is described in the next section.

## Groups and Permissions

Projects are encouraged to use groups to manage access to resources, including files and directories/folders in the `arc` project storage, mounted at `/arc/projects` in every session.

Groups and their memberships can be managed through the CANFAR groups web interface, here: https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/

Once created, groups can be assigned to files and directories in arc storage directly from their interactive sessions, or through the [CANFAR storage](https://www.canfar.net/storage/arc/list)

For more details on setting access permissions, see the documentation on [file permissions](permissions.md)

## Programmatic Access

Session launching and management are through the `skaha` service. The `skaha` API definition and science platform service are here:  https://ws-uv.canfar.net/skaha

## Community and Support

Discussions of issues and platform features take place in the Science Platform Slack channel: [Science Platform Slack Channel](https://cadc.slack.com/archives/C01K60U5Q87)

To report bugs and request new features, please use our GitHub pages: 
- For the infrastructure and session, https://github.com/opencadc/science-platform/issues
- For the containers: https://github.com/opencadc/science-containers/issues

Contributions to the platform (including updates or corrections to the documentation) can be submitted as pull requests to this GitHub repository. We especially encourage science containers to be shared across the user community by making your published containers public.

General inquiries can be made to [support@canfar.net](mailto:support@canfar.net), and take a look at our [FAQ](faq.md).

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
