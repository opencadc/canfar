# CANFAR Science Platform FAQ

* ***My session is stuck in the `Pending` state*** - This can imply that the platform is unable to launch your image.  There are a number of potential causes:
   * Often skaha fails to authorize you to https://images.canfar.net due to an expired `CLI Secret`.  Try resetting this value by logging into https://images.canfar.net (using the OIDC Login button), going to your User Profile, and updating your CLI Secret.  Once done you should delete the Pending session and try launching it again.
    * If the image is proprietary and the CLI Secret update did not work, check with your project administrator to ensure you have been granted access to the project in https://images.canfar.net
    * The session could be in a Pending state waiting for resources so that it can be scheduled.
    * More information about the reason for the Pending state can be found using the logging mechanisms explained in [Programmatic Access](#programmatic-access).

* ***How do I test a graphical container on my Mac?***


1. Enable "Allow connections from network clients" in XQuartz settings. Relaunch XQuartz.
2. In terminal execute

        > xhost + 127.0.0.1

3. Launch docker run with the option

        -e DISPLAY=host.docker.internal:0

These steps were taken from https://medium.com/@mreichelt/how-to-show-x11-windows-within-docker-on-mac-50759f4b65cb

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
