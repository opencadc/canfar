# CANFAR Science Platform Headless Jobs

Please contact us before making use of the 'headless job' support--we are incrementally adding support for batch processing in the science platform.

#### Create an image

Create an image as per the regular process of making containers available in the platform:  [Publishing](PUBLISHING.md)

However, label it as `headless` in https://images.canfar.net to make it available for headless job launching.

#### Launch a headless job

For the full details of the job launching API, see this section of the akaha API documentation:  https://ws-uv.canfar.net/skaha#!/Session_Management/post_session

All jobs will be run as the calling user.  All jobs have the `/arc` filesystem mounted.

##### With a publically available Image
Example: overriding the command and providing two arguments:

```sh
curl -E ~/.ssl/cadcproxy.pem https://ws-uv.canfar.net/skaha/v0/session -d "name=headless-test" -d "image=images.canfar.net/skaha/terminal:1.1.2" --data-urlencode "cmd=touch" --data-urlencode "args=/arc/home/majorb/headless-test-1a /arc/home/majorb/headless-test-1b"
```

##### With a private Image
Example: overriding the command and providing two arguments:

1. Obtain your Image Registry secret.
    1. Login to the [Harbor Image Registry](https://images.canfar.net)
    1. In the top right, click on your Username, then click on `User Profile`.
    1. At the bottom of the `User Profile` modal dialog, there is a `CLI secret` field.  Click on the `Copy` icon to copy your secret into the clipboard.  
    ![CLI Secret Field](./cli-secret-field.png)
1. With the CLI secret in your clipboard, create a string with your username and secret, separated by a colon (`:`), and Base64 Encode it:
```sh
ENCODED_HEADER=`echo -n "myusername:my-secret" | base64 -i -`
```
1. Now use that in the session create command:
```sh
curl --header "x-skaha-registry-auth: ${ENCODED_HEADER}" -E ~/.ssl/cadcproxy.pem https://ws-uv.canfar.net/skaha/v0/session -d "name=headless-test" -d "image=images.canfar.net/skaha/terminal:1.1.2" --data-urlencode "cmd=touch" --data-urlencode "args=/arc/home/myusername/headless-test-1a /arc/home/myusername/headless-test-1b"
```

**Note**
The CLI Secret _may_ need to be periodically refreshed from the Harbor page; simply repeat the process from 1.1 above.

On a successful launch from a public or private image, skaha will return the `sessionID` on a post (job launch).  The job will remain in the system for 1 hour after completion (success or failure).

Job phases:
- Pending
- Running
- Succeeded
- Failed
- Terminating
- Unknown

To view all sessions and jobs:
```curl -E ~/.ssl/cadcproxy.pem https://ws-uv.canfar.net/skaha/v0/session```

To view a single session or job:
```curl -E ~/.ssl/cadcproxy.pem https://ws-uv.canfar.net/skaha/v0/session/<sessionID>```

To view logs for session:
```curl -E ~/.ssl/cadcproxy.pem https://ws-uv.canfar.net/skaha/v0/session/<sessionID>?view=logs```

This shows the complete output (stdout and stderr) for the image for the job.

To view scheduling events for session:
```curl -E ~/.ssl/cadcproxy.pem https://ws-uv.canfar.net/skaha/v0/session/<sessionID>?view=events```

Scheduling events will only be seen when there are issues scheduling the job on a node.

## Community and Support

Dicussions of issues and platform features take place in the Science Platform Slack Channel:  [Science Platform Slack Channel](https://cadc.slack.com/archives/C01K60U5Q87)

Reporting of bugs and new feature requests can also be made as github issues:  https://github.com/opencadc/skaha/issues

Contributions to the platform (including updates or corrections to the documentation) can be submitted as pull requests to this GitHub repository.

General inquiries can be made to [support@canfar.net](mailto:support@canfar.net)

## FAQ

* ***My session is stuck in the `Pending` state*** - This can imply that the platform is unable to launch your image.  There are a number of potential causes:
   * Often skaha fails to authorize you to https://images.canfar.net due to an expired `CLI Secret`.  Try resetting this value by logging into https://images.canfar.net (using the OIDC Login button), going to your User Profile, and updating your CLI Secret.  Once done you should delete the Pending session and try launching it again.
    * If the image is proprietary and the CLI Secret update did not work, check with your project administrator to ensure you have been granted access to the project in https://images.canfar.net
    * The session could be in a Pending state waiting for resources so that it can be scheduled.
    * More information about the reason for the Pending state can be found using the logging mechanisms explained in [Programmatic Access](#programmatic-access).

* ***How do I test a graphical container on my Mac?***
   * See the instructions to have container display shown on your Mac here:  [Display ENV on OSX](DISPLAY_ENV_ON_OSX.md)

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
