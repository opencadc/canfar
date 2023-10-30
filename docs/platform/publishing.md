# CANFAR Science Platform Containers

## Introduction

The CANFAR Science Platform supports various types of containers: `session`, `software`,  and `legacy desktop application`

- `Session` are containers launched as native browser interactive applications (i.e. HTML5/Websocket).
- `Software` are containers launched with any kind of executable, installed with custom software stack. 
- `Legacy desktop application` are containers launched and viewed specifically through a desktop `session`.  

## Building CANFAR Science Platform Containers

### Minimum requirements
- Containers must be based on a standard Linux x86_84 distribution.
- Containers must contain an SSSD client and have ACL capabilities if one want to interact with the `arc` storage

#### SSSD and ACL
For linux group id (`gid`) names to be resolved, the container must have an SSSD client and ACL tools installed, and must provide an `nsswitch.conf` file as described below.  If any of these are missing, only group IDs will be displayed (when `id` is typed for example), but file system authorization will continue to work as expected.
The packages to install on a Debian-based Linux distribution are `sssd-client` and  `acl`.

The file `/etc/nsswitch.conf` must include the `sss` module in the `passwd`, `shadow`, and `group` entries.  For example:

```
passwd:     sss files
shadow:     files sss
group:      sss files
```

### Additional requirements for legacy desktop application containers
Examples of legacy desktop software containers are astronomy GUIs such as CASA, Topcat, Aladin, and customized containers such as Gemini processing containers which require desktop interaction. 
Some of the recipes (Dockerfiles) for building these containers can be found in the [desktop directory](desktop).  They can also be managed and hosted elsewhere. However, wherever the source is hosted, containers must meet a minimal set of requirements and expectations for execution in skaha.
Also the default executuable is `xterm`, so ensure it is installed.

Note: the desktop session is also sometimes known as the ARCADE software environment.

## Initialization and Startup

#### Running container process owners
Containers in the CANFAR Science Platform are always executed as the *CADC User* and never as root. Operations that require root must be done at the build phase of the image.  If runtime root access is required, it can possibly be done by giving sudo access to specific actions.

#### Session container initialization
Initialization for session containers is based on the session container *type*.  There are currently four types with different startup procedures:
1. `notebook`: it requires a `jupyter lab` executable
1. `carta`: initialization and startup is done through a customized script
1. `desktop-app`: desktop session startup is managed by the skaha infrastructure.
1. `contributed`: it will follow a customized startup script

There may be multiple versions of the same type of session container, but the startup procedure for these must remain the same for them to be of the same type.

#### Contributed session containers
Contributed sessions are for custom-build, web-browser applications that are not officially created and maintained by CANFAR.
The rules of building a container of type "contributed" on the CANFAR Science Platform are:
1. Incoming trafic will be over http (which may include websocket trafic) on port 5000
1. From the point of view of the container, requests will be received at the root path (/), but URLs in the browser will look like https:///, where <host> and <path> are subject to change. This path will initially be https://ws-uv.canfar.net/sessions/contrib/<sessionid>
1. The instance will be started by a script in the image that must be available at /skaha/startup.sh and will be passed 1 parameter: the sessionid.

#### Software container initialization

The `CMD` and `EXECUTABLE` directives in a CANFAR container `Dockerfile` will be ignored on startup.  Instead, bash within an xterm will run. `CMD` and `EXECUTABLE` are still useful for testing containers outside of CANFAR.

If the container needs to do any runtime initialization, that can be done in a script named `init.sh` in the `/skaha` root directory.  This script **must not block** and needs to return control to the calling process.

If `/skaha/init.sh` is provided, a sensible directive for testing the container via docker is `CMD ["/skaha/init.sh"]`

Another option is for containers to make available a file named `/skaha/startup.sh`.  If it exists, it will be called with a single parameter, which is the command `startup.sh` must run in order to execute on the platform.  So, the end of `startup.sh` should do: `exec "$@"` to execute the incoming parameter.  Containers should use startup.sh when environment must be made available to the context of the application.

<a name="publishing"></a>
## Publishing skaha containers

### Step 1: Create a harbor account
The CANFAR Science Platform hosts a private container registry. It is an instance of the [Harbor](https://goharbor.io/) open source project as a container registry. Session and software containers launched can be launched from this registry.

If you have logged into harbor before then step 1 can be skipped.

1. Go to https://images.canfar.net
2. Press the `Login with OIDC Provider` button.
3. Enter your CADC username and password.
4. When prompter for a harbor userid, use your CADC username.

After these steps you now have a harbor account and can see the project containers through its interface. If you wish to publish to any of the projects, contact the project admistrator (or contact support@canfar.net) and ask for 'Development' access to the project.

### Step 2: Docker login to harbor
1. From the harbor portal, go to the top right, click on your username, then go to 'User Profile'.
2. Set your CLI secret -- this is the password to use for `docker login` commands.  You can copy the existing, generated secret, or 'upload' (enter) your own.
3. From the computer on which you have built the docker image you wish to publish, do a docker login:

```docker login images.canfar.net```

Your user is your CADC username, and your password the value of the CLI Secret mentioned above.

### Step 3: Push your image to your project
1. On the same computer, find the `IMAGE ID` of the image you'd like to push with the command

```docker images```

2. Tag the image for harbor:

```docker tag <IMAGE ID> images.canfar.net/<PROJECT>/<MY IMAGE NAME>:<IMAGE VERSION>``` 

where:
   * `<PROJECT>` is the project to which you've been granted Developer access.
   * `<MY IMAGE NAME>` is the name of the image you are publishing.
   * `<IMAGE VERSION>` is the version of the image.
   
3. Push the image to harbor, with:

```docker push images.canfar.net/<PROJECT>/<MY IMAGE NAME>:<IMAGE VERSION>```

### Step 4: Label your image type

1. Go back to https://images.canfar.net
2. Click on your project, then on your newly pushed image (also called a repository in harbor).
3. Select the 'artifact' with the correct version (tag).
4. Under the 'Actions' drop-down, apply the approripate label to the artifact.

## Science Platform Actions

A number of the steps below can be done using the CANFAR Science Platform Portal at https://www.canfar.net

### Listing images on CANFAR

Once publishing and labeling has been completed, the image will be visible.  It can then be seen on the Science Platform Portal, or with the folowing command:

```curl -E <cadcproxy.pem> https://ws-uv.canfar.net/skaha/v0/image```

### Listing resource contexts

The available cores and RAM in skaha can be seen from the Science Platform, or viewed with:

```curl -E <cadcproxy.pem> https://ws-uv.canfar.net/skaha/v0/context```

<a name="launching"></a>
## Launching containers

### Session containers

1. Use the Science Platform Portal or this curl command to launch your newly published image:

```curl -E <cadcproxy.pem> https://ws-uv.canfar.net/skaha/v0/session -d "name=<arbitrary-name>" -d "image=images.canfar.net/<PROJECT>/<MY IMAGE NAME>:<IMAGE VERSION>"```

If non-default values for cores and/or ram is preferred, the parameters `-d cores=<cores>` and `-d ram=<ram>` can be added to the session launching command above.

2. Use the Science Platform Portal or this curl command to find the URL to your session:

```curl -E <cadcproxy.pem> https://ws-uv.canfar.net/skaha/v0/session```

If this is the first time this image has been launched in may take a few minutes for the cloud do retrieve the image from harbor and send it to the selected node.

### Software containers
It should just run as is. See also [headless containers](HEADLESS.md).

### Legacy desktop application containers

Once a legacy desktop software container has been pushed to harbor, it must be labelled with `desktop-app`.

To then make it appear in the `Applications->Astro Software` menu on the desktop a new desktop session must be started.

The desktop menu items in `Applications->Astro Software` are organized by harbor project.  A sub-folder is created for each project.  Then, each version of the artifacts (images) within that project will be displayed in the project sub-folder.  For example, the desktop-app image identified by URI:

```images.canfar.net/skaha/terminal:1.0```

will be placed in the desktop menu like so:

```Applications -> Astro Software -> skaha -> terminal:1.0```

<a name="testing"></a>
## Testing
Before publishing a new or modified image, testing should be done to ensure it works as expected.

For session containers, nearly all testing can be done by using `docker` to run the image.  A port should be exposed so you can connect your browser to the locally running session.

For legacy desktop application containers, docker will not be able to provide a graphical display of CASA windows, so most testing must be done in a skaha-desktop instance running in the cloud.

The only requirement for a container is to ensure the web application to be launched with a `/skaha/startup.sh` script in the container, and the web application running on port 5000.

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
