# Changelog

## [1.0.2](https://github.com/opencadc/canfar/compare/v1.0.1...v1.0.2) (2025-09-16)


### Bug Fixes

* **defaults:** updated default config to use v1 server api ([447b17e](https://github.com/opencadc/canfar/commit/447b17ec37072bf6b08d279baafe7f8d561d6afd))
* **session:** default destroy_with not targets `Completed` jobs ([08581be](https://github.com/opencadc/canfar/commit/08581bed48b4530142ae54418ff6b168655dee5b))
* **sessions:** image parameter now is not locked down to images.canfar.net to support local variations in all SRCnet deployments ([2b69c52](https://github.com/opencadc/canfar/commit/2b69c521b7757a390b97aaac677eecffa8ae4b8b))
* **sessions:** removed no longer needed view=event param during http get ([6afb91c](https://github.com/opencadc/canfar/commit/6afb91c10b6309090128425331e8e2267e525794))


### Documentation

* overhaul and clarify platform guides, containers, sessions, storage, permissions, and mkdocs config ([db52b02](https://github.com/opencadc/canfar/commit/db52b025ccda768fc113b735381a9bc2c3c81b69))
* **release-notes:** consolidation ([7cbebae](https://github.com/opencadc/canfar/commit/7cbebae106ebc45b902a90c6da625b7ce4b69521))
* **updates:** for breaking changes between v0 and v1 api ([d58bd6c](https://github.com/opencadc/canfar/commit/d58bd6cf173cc4cf2394a2062a446ab85b8b1def))

## [1.0.1](https://github.com/opencadc/canfar/compare/v1.0.0...v1.0.1) (2025-09-11)


### Bug Fixes

* correct typos in release notes ([def5f3c](https://github.com/opencadc/canfar/commit/def5f3c6f966f5857f850a53456d6b080ecfc75f))


### Documentation

* **about-page:** removed outedated governance info ([16ff6cc](https://github.com/opencadc/canfar/commit/16ff6ccf6ec2d7a78aa171cd731d6cd028a3827e))
* **alma:** fix image paths to sessions/images where needed ([a8524e7](https://github.com/opencadc/canfar/commit/a8524e74467f75e9a0b31b7d75772cb7553c4928))
* **batch:** fix CLI and API syntax errors ([160b801](https://github.com/opencadc/canfar/commit/160b801a066750ca5dc82ebdf3706ffaf147b218))
* **cleanup:** fixes for relatives paths, removed redundant toc in platform docs, fixes docstrings ([390d10b](https://github.com/opencadc/canfar/commit/390d10be37a5be4905b5793d62350788ced68551))
* **release-notes:** add CanfarSP 2025.1 announcement and version info ([30c61d1](https://github.com/opencadc/canfar/commit/30c61d13692afad49453174a29c6d980068dd4eb))
* **release-notes:** fixes ([4aaf24b](https://github.com/opencadc/canfar/commit/4aaf24b8d2bd815ea00fa6914b27a77274c448f5))
* **release-notes:** update release notes ([9f73c77](https://github.com/opencadc/canfar/commit/9f73c77d54859926c22e4ff50b0839c8410e3215))
* **release-notes:** v1.0.1 ([d4d4d0d](https://github.com/opencadc/canfar/commit/d4d4d0d1d947b0094e65fa64cd3f16015ff77de3))

## [1.0.0](https://github.com/opencadc/canfar/compare/canfar-v0.8.0...canfar-v1.0.0) (2025-09-09)


### ⚠ BREAKING CHANGES

* **project:** - The configuration directory has moved from `~/.skaha` to `~/.canfar`.

### Features

* **api:** added support for flexible user sessions ([c9b5b98](https://github.com/opencadc/canfar/commit/c9b5b986bcf933b364276f2c02146201a6829998))
* **auth:** add HTTPx authentication hooks for token refresh ([489066d](https://github.com/opencadc/canfar/commit/489066d560d883f1bad77521e6fa5a02e754b494))
* **auth:** add OIDC authentication hooks for automatic token refresh ([bc4596f](https://github.com/opencadc/canfar/commit/bc4596fdad62db016a7cc81f00150a5fd2e85150))
* **auth:** added oidc device flow logic ([1013cf5](https://github.com/opencadc/canfar/commit/1013cf551dceaafeeed25a2e1fdd11a8c375c9d5))
* **auth:** added x509 cert get logic ([657a97d](https://github.com/opencadc/canfar/commit/657a97de3c455e8ab26c1eb84a4dd794f4ebd5eb))
* **auth:** implement async and sync OIDC token refresh functions ([b43b05f](https://github.com/opencadc/canfar/commit/b43b05f60c70c8c95d2b4e9e6052df44b2e35d59))
* **auth:** server info is now saved for each auth config ([1788c1e](https://github.com/opencadc/canfar/commit/1788c1e35a93142b47a20c2d71c5f8609a40d05b))
* **build:** added edge container build and attestation ([d07e008](https://github.com/opencadc/canfar/commit/d07e008dd8c4de36a8e20ca50f5a91dc03f8afd4))
* **cli:** added `skaha open` command to open sessions in a web browser. Made skaha info more readable ([c932187](https://github.com/opencadc/canfar/commit/c932187838c8c2f2a544dbde396ea79b484b661e))
* **cli:** added auth cmds: list, switch, rm & purge ([6ab0bd8](https://github.com/opencadc/canfar/commit/6ab0bd8c15c14fdbd5ada3c75bf68af022e7c186))
* **cli:** added capability to discover vosi capabilities of a server ([da70dde](https://github.com/opencadc/canfar/commit/da70ddeb3d419c5aa2ecb60786af0b4dd3de0676))
* **cli:** added entrypoing cf ([cf3fce8](https://github.com/opencadc/canfar/commit/cf3fce8dc49fc7c763bab218dd896a0ff22bb414))
* **cli:** added feat to auto discover skaha servers ([46eb565](https://github.com/opencadc/canfar/commit/46eb565e00e3bf4ff95020d87f15a93d64f16d4a))
* **cli:** added list, ls to skaha ps as aliases ([c88eb6a](https://github.com/opencadc/canfar/commit/c88eb6ab7369dd88a3e7b27e58a9c751f403e917))
* **cli:** added support for using the CLI as canfar ([5051af1](https://github.com/opencadc/canfar/commit/5051af190e188d2231d9aea98056b52d2eb65725))
* **client:** add expiry property and enhance SSL context handling for authentication ([cb6261a](https://github.com/opencadc/canfar/commit/cb6261aaad67126c32ac350de42777ea8ae21d6f))
* **client:** added logic to catch AuthExpiryError when the auth context is expired ([49c106e](https://github.com/opencadc/canfar/commit/49c106e6c0594197c1dd03c4b47daeafb768f790))
* **client:** added loglevel to configure the python logging levels ([431f46d](https://github.com/opencadc/canfar/commit/431f46dd4abebff53edb1485a5d5064ef432f3bf))
* **client:** added token support to skaha client ([6c7c748](https://github.com/opencadc/canfar/commit/6c7c7486b6a078a77b5a6b42e2c8162d95ff80f7))
* **client:** enhance SkahaClient documentation and improve authentication handling ([1e6b770](https://github.com/opencadc/canfar/commit/1e6b7708d009a207ccf60ee8aaa233df26f8ef97))
* **client:** significant improvements to the base skaha client to support context managers ([a197553](https://github.com/opencadc/canfar/commit/a19755376984a338e8ea56d73f9bec71463c7a34))
* **client:** updated skaha client to use httpx instead of requests ([4c10de8](https://github.com/opencadc/canfar/commit/4c10de87451e9687fe29c17f363e5736b36e8203))
* **cli:** work-in-process ([2e646ab](https://github.com/opencadc/canfar/commit/2e646ab2586701f908d78844f94a3bc41b0c6a65))
* **codecov:** added badge ([373412d](https://github.com/opencadc/canfar/commit/373412d8f8b6a806b111a5d8dac89c64a876d6b3))
* **config:** updated auth config to provide valid & expired checks for all auth types and added tests ([4dc6929](https://github.com/opencadc/canfar/commit/4dc6929b7538d3a230a9c1d4c3a134ec9835ec7c))
* **context:** updates to context.resources api ([4d08876](https://github.com/opencadc/canfar/commit/4d08876de0b49201ddef0b8c9ddc01f022fcf11f))
* **discover:** added functionality to discover skaha servers from registries and also added tests ([5857772](https://github.com/opencadc/canfar/commit/5857772563d354ad0ad5a90c0620b4689f904b54))
* **dockerfile:** added base dockerfile for the project ([28f7e51](https://github.com/opencadc/canfar/commit/28f7e5120d500081c44083f1141eeeacf89e1305))
* **docs:** added docs about canfar ([297156c](https://github.com/opencadc/canfar/commit/297156c9820a7378d6e173dcf7b3c9101f92886e))
* **docs:** added docs about canfar ([76b69b1](https://github.com/opencadc/canfar/commit/76b69b13b840dc7ca61cbbaca7fa322ecacb4e8c))
* **docs:** added realease notes ([18a0d30](https://github.com/opencadc/canfar/commit/18a0d3061475635f32c87b11a0041d42bca75a2a))
* **docs:** importing science container docs with history ([f388602](https://github.com/opencadc/canfar/commit/f3886023eef48f8b4d99ee32dbc102a791602dc6))
* **docs:** reorg from scicon docs ([85ca36c](https://github.com/opencadc/canfar/commit/85ca36c1c1a96b08ad14726f38658112be1921df))
* **docs:** significant updates for client docs to provide sync/async variations of most python calls ([7eacf8f](https://github.com/opencadc/canfar/commit/7eacf8f5440e81286b53a81bb53b064fb558d962))
* **docs:** significant updates for client docs to provide sync/async variations of most python calls ([c86ae6b](https://github.com/opencadc/canfar/commit/c86ae6b4ccbe21d18104f2c6cca6028a5e08e180))
* **docs:** updated README, and the cleaned up the main landing page significantly ([4618ed2](https://github.com/opencadc/canfar/commit/4618ed286e989375e775613e22d10ac03b858346))
* **docs:** updated README, and the cleaned up the main landing page significantly ([2745b60](https://github.com/opencadc/canfar/commit/2745b60f5a23c8058e9a14c3b63cf690f9cbade0))
* **docs:** updates to documentation theme and features ([5289571](https://github.com/opencadc/canfar/commit/5289571f84fd4d81f723f31d688f0a70d2f6e0b8))
* **exceptions:** added skaha exception classes ([0651191](https://github.com/opencadc/canfar/commit/0651191ace890b489af64af6cd49cd892871fe38))
* **garble:** added fernet and rot13 ciphers to encrypt/obsfucate sensitive info ([7204879](https://github.com/opencadc/canfar/commit/72048791e297c46cd4a2d738ae4a25dc545348ff))
* **github-actions:** added pypi release action and updated client payload ([b0b3593](https://github.com/opencadc/canfar/commit/b0b3593d7166559032de099cf829a96203126f78))
* **helpers:** added code to to split tasks for large scale processing ([6ffe5cb](https://github.com/opencadc/canfar/commit/6ffe5cb3328628f3782477d2927b2b458e477bc8))
* **hooks:** added cli tool typer hook for multiple command aliases ([6c5bc15](https://github.com/opencadc/canfar/commit/6c5bc150f969bf49edd14273a4aaef80f31fa57b))
* **logging:** added comprehensive rich based logger for the project ([a48c520](https://github.com/opencadc/canfar/commit/a48c520390db965825a0053722789cdb31812dab))
* **logs:** added stdout for printing logs in terminal ([0c34cad](https://github.com/opencadc/canfar/commit/0c34cada7fee945d710727222b27e17e7d46bd06))
* **models:** added http models for the client ([0679e8f](https://github.com/opencadc/canfar/commit/0679e8f86055f01a4e54b4c63fe8e77ddc8d88b6))
* **models:** added supported auth tracking to upstream servers model ([7098327](https://github.com/opencadc/canfar/commit/7098327a5d984031433996d216453c3ccf163004))
* **models:** all client models have been moved to skaha.models ([a07c676](https://github.com/opencadc/canfar/commit/a07c6760ff824a6dcc647a67be2a9abcc27cf52d))
* **oidc:** added tests and made the oidc auth flow async ([0059e12](https://github.com/opencadc/canfar/commit/0059e128015e737ec3f008bf01afb5aa2b667392))
* **project:** This commit renames the project from `skaha` to `canfar` to align with the official support from CADC and create a unified naming scheme for the science platform ([ecf55fb](https://github.com/opencadc/canfar/commit/ecf55fb6c1d91d9b455a7b96d51e0b98c220895e))
* **session:** added new feature to delete sessions with name prefix, kind and status ([056254b](https://github.com/opencadc/canfar/commit/056254b9143daa2721486b801093598f1dbc7baa)), closes [#37](https://github.com/opencadc/canfar/issues/37)
* **session:** added session.events to show deployment events on the cluster, e.g. loading container image etc ([58e9bca](https://github.com/opencadc/canfar/commit/58e9bca90652ffcbcca8eeaecf351123254d62c0))
* **sessions:** added skaha AsyncSession ([2693272](https://github.com/opencadc/canfar/commit/26932724e4533bf1823cfad97e3b9ccc8ef5fd7b))
* **sessions:** added support for firefly ([87d16c1](https://github.com/opencadc/canfar/commit/87d16c1637d5848fbc522c3340c611df40f6d2fa))
* **tests:** add comprehensive tests for OIDC authentication and HTTPx hooks ([be7fb50](https://github.com/opencadc/canfar/commit/be7fb505127cfa2496a852316e3601520cc27d37))
* **types:** added mode, which reflects the auth type of the client ([5781e4a](https://github.com/opencadc/canfar/commit/5781e4ad2c39be0faea78a6a814bb58c0d8cec79))
* **types:** updated to the auth data model ([7f293c4](https://github.com/opencadc/canfar/commit/7f293c43a1a028be38a27787a44f1d781580acc7))
* update release-please configuration and versioning for CANFAR ([b71a8d1](https://github.com/opencadc/canfar/commit/b71a8d1af147742cee8bfbe8b0a2b9b726d61eb9))


### Bug Fixes

* **api:** httpx error catching hook now re-raises the errors rather than execessive printing in stdout ([6b7aa71](https://github.com/opencadc/canfar/commit/6b7aa71a3ff69c06e2110e53e662d2abdfdd135e))
* **api:** httpx error catching hook now re-raises the errors rather than execessive printing in stdout ([827205f](https://github.com/opencadc/canfar/commit/827205f92922be7b0c71eaf4f0a0a6bd24c739b0))
* **api:** updated context, images, overview with httpx ([391e857](https://github.com/opencadc/canfar/commit/391e85732dc324b1d2dee51c4d46d558e5d7d72f))
* **attestation:** added attestation for dockerhub container image ([0ff4ba2](https://github.com/opencadc/canfar/commit/0ff4ba2b321d61483325018d42f39c97d22eb3cb))
* **auth, config, http:** refactor imports and clean up default handling in models ([6095a09](https://github.com/opencadc/canfar/commit/6095a09b3a94a01ac509dc3f8b9937c5d754c472))
* **auth, config, models:** refactor authentication handling and improve configuration properties ([aaa8c61](https://github.com/opencadc/canfar/commit/aaa8c618dd4c9de6314437a170e33d5f63328ced))
* **auth:** added comprehensive login support ([bd11fe4](https://github.com/opencadc/canfar/commit/bd11fe4f27e473a7461112d4f9e881bf6858dbb7))
* **auth:** default x509 cert expiry is now 30 days, similar to cadc-get-cert ([f0bd2a7](https://github.com/opencadc/canfar/commit/f0bd2a70b1987c971f94970501b123dd61505ded))
* **auth:** improve login flow and server selection logic ([18b8d6d](https://github.com/opencadc/canfar/commit/18b8d6d881e5d70b9ee9f728a982ba13034b8fe6))
* **auth:** oidc auth now properly displays qr code and manual links before trying to open webbrowser ([1c756f9](https://github.com/opencadc/canfar/commit/1c756f954c7d4c492ef036377886447456502458))
* **auth:** x509 expired now return True when there is no cert to be found ([2ab7141](https://github.com/opencadc/canfar/commit/2ab71416106aa107d06c773e3af641eba387f95d))
* **auth:** x509 now has better exception handling ([a4469b3](https://github.com/opencadc/canfar/commit/a4469b3282fc32c3bc2e4dae5fd11e8dda89c3c3))
* **badge:** update to codeql bagde url ([c95b6e0](https://github.com/opencadc/canfar/commit/c95b6e075c8c81f079bca7936940da01645f04a7))
* **ci:** fix to edge container build ([59924bd](https://github.com/opencadc/canfar/commit/59924bd8193f609ec2e958eea59a333469d41de3))
* **ci:** improved secret cleanup ([990c5a1](https://github.com/opencadc/canfar/commit/990c5a1e461843db681417bb229bcb51c13d8aed))
* **cleanup:** comments ([8a1a078](https://github.com/opencadc/canfar/commit/8a1a0785232c404b5b0b68cbd4b8b0349d09a34c))
* **cli:** added a new aliases section to cleanup the l&f of the cli ([6165575](https://github.com/opencadc/canfar/commit/6165575887826b0acf8dc8e2f59f21b08e946606))
* **cli:** added new aliases for list and create, fixed added `Terminating` state for Status models ([a7e946d](https://github.com/opencadc/canfar/commit/a7e946de8730a23609439bdb52a227ae576eaafa)), closes [#103](https://github.com/opencadc/canfar/issues/103)
* **cli:** auth now search for dev registries only when running with --dev flag ([c490b46](https://github.com/opencadc/canfar/commit/c490b469cf7a0152c38b4c993a5d8d93c0e9d382))
* **cli:** config - added path ([30f2617](https://github.com/opencadc/canfar/commit/30f26178f8ead4286f14dbcc77095d9323198e7b))
* **cli:** create options cpus changed to cpu ([05081ed](https://github.com/opencadc/canfar/commit/05081ed6b528e0688f5a42a1fa514672cea7582b))
* **cli:** deprecated skaha & cf as entrypoints ([6ea71de](https://github.com/opencadc/canfar/commit/6ea71dec27e8f81505f1db3e525b9e5357553bf0))
* **cli:** desktop-app info problems ([6b37351](https://github.com/opencadc/canfar/commit/6b37351a3adab0ca7f6edc2ef8f46d94620b9c0c))
* **client, overview:** refactor base URL handling to use 'url' attribute instead of 'server' ([b429820](https://github.com/opencadc/canfar/commit/b429820807398c55b9b83f128a79f51f893d9c64))
* **client:** added fix for better printing of erorr msgs ([72dd666](https://github.com/opencadc/canfar/commit/72dd666e8d2e2aa9f4ae7e4ab1d11fe59926d197))
* **client:** changed to the default and max values of parallel conns ([ce552bf](https://github.com/opencadc/canfar/commit/ce552bff74602c3525154a5ef4308d9291e9cc53))
* **client:** deprecated client.verify since it no longer affects any logic ([9eed6e9](https://github.com/opencadc/canfar/commit/9eed6e95db5eadc45ed084bde5eab1cdab7ca727))
* **client:** fixed annotation issues for client, asyncClient ([889a6a8](https://github.com/opencadc/canfar/commit/889a6a8f9072cf663c10d648248e0a2928ba8873))
* **client:** http client now properly adds the refresh hook before the expiry hook ([b340308](https://github.com/opencadc/canfar/commit/b340308bdb0b092d010da5a4486c4aaa6b0fe7d9))
* **client:** the skaha client on performs x509 checks when creating the clients ([b6c3b80](https://github.com/opencadc/canfar/commit/b6c3b80fa84d990995496aa695bc7ad7d51f875b))
* **cli:** fetch response model, utilization calc ([266b8eb](https://github.com/opencadc/canfar/commit/266b8ebf4b45bca59a11755452ba6d7957fd2cfb))
* **cli:** fetch response, now only inits startTime & expiry time to now, if it cannot parse the input timestamps ([79ea7f4](https://github.com/opencadc/canfar/commit/79ea7f43bc9cf6d622237fb74f86b1c091e06a73))
* **cli:** fetchResponse model relaxed for expireTime ([b082632](https://github.com/opencadc/canfar/commit/b082632ece5397f15b4ed302cbcbbdb8acf5268e))
* **cli:** fix for stats output print statement ([856df95](https://github.com/opencadc/canfar/commit/856df95171ae433bc5a5d6759a59d7ccc2a549b2))
* **cli:** fixed the max request sizes in stat output ([1f55f1e](https://github.com/opencadc/canfar/commit/1f55f1e01e0d7a35ad4093c6a10cf614165aa002))
* **cli:** fixed version selection issue on login ([3349c5b](https://github.com/opencadc/canfar/commit/3349c5b887640df762c9db56ccb7fa127dff6698))
* **cli:** fixed version selection issue on login ([79f3ca8](https://github.com/opencadc/canfar/commit/79f3ca8a133e288b1285d3416b3e4229cee00582))
* **cli:** numerous fixes for general look and feel, updated usage and help to be more descriptive ([ea59085](https://github.com/opencadc/canfar/commit/ea59085b359d040cc219d5e76680b354d9ad593b))
* **cli:** ps,list,ls are now sorted by startTime ([fdf34ed](https://github.com/opencadc/canfar/commit/fdf34edc957545cf2f74eb4887b51b7099a38f2d))
* **cli:** relaxed fetch response requirements further ([1ea157c](https://github.com/opencadc/canfar/commit/1ea157c40b719d7c588154c067c19725aabea6c6))
* **cli:** relaxed FetchResponse model requirements ([3801578](https://github.com/opencadc/canfar/commit/3801578d7717eaca3505ea3232a0f667aa715fcf))
* **cli:** relaxed requirements for fetchResponse ([0856e76](https://github.com/opencadc/canfar/commit/0856e765da79ade7ece6bef2536d2f9a63dd3c3f))
* **cli:** remove canfar list, and canfar rm as aliases due to conflicts with linux commands ([e1a4742](https://github.com/opencadc/canfar/commit/e1a47421e18ed749ab10b11210ff3252d2086488))
* **cli:** stats now report usage instead of requested, and the output is much more aligned with the platform ui ([71662ed](https://github.com/opencadc/canfar/commit/71662ed823bac049d1d1d97458a68fa59a2d523f))
* **cli:** updated the discover logic to be cleaner ([ebff177](https://github.com/opencadc/canfar/commit/ebff177eab097de019cc13bb7876abf59b850762))
* **contribution:** updated guidelines ([bc5400e](https://github.com/opencadc/canfar/commit/bc5400e9b2901d76a53c502d10688bf7f9361dfa))
* correct typos and misleading statements in release notes ([d89cdca](https://github.com/opencadc/canfar/commit/d89cdca8a41d8a1e5db446ba10453f7dc84833fd))
* **dockerfile:** fix to stage names ([f46b081](https://github.com/opencadc/canfar/commit/f46b081dc6d9e7013e23f99e5e4e41e755dac81a))
* **docker:** fix for docker build due to uv path install changes ([00fd5de](https://github.com/opencadc/canfar/commit/00fd5de260793d00b33d65216058c94854e73133))
* **docs:** added community landing page ([03236f7](https://github.com/opencadc/canfar/commit/03236f7ba1ce9812e0b346c9853981b71ac5929b))
* **docs:** added ico, logo and fixed docker link to harbor ([d73b7c6](https://github.com/opencadc/canfar/commit/d73b7c6720ee1b22730abad6e1d627b4cd43bd2e))
* **docs:** changed the location of legacy docs ([0ef7e43](https://github.com/opencadc/canfar/commit/0ef7e436de5e892a7a3e08c28c6f67ffc6b215ea))
* **docs:** cli ([a24287d](https://github.com/opencadc/canfar/commit/a24287da0386f8c6f83ac84874f294790e26aafa))
* **docs:** formatting ([62ca659](https://github.com/opencadc/canfar/commit/62ca659b5043af7b3294e937815a6e14ed1aa0a0))
* **docs:** improve docstrings for clarity and consistency across authentication modules ([48599d3](https://github.com/opencadc/canfar/commit/48599d3dd683d68af242b433e339a2018f382f93))
* **docs:** improve formatting of docstring for gather function parameters ([9807194](https://github.com/opencadc/canfar/commit/980719411abdcc2c67df00dd6ca3419e0f822424))
* **docs:** remove slow tests details and clarify slow test marking criteria ([18999b7](https://github.com/opencadc/canfar/commit/18999b74bf652eb6eefbd4887b9128854db15250))
* **docs:** updated doc/status/badge links ([6efed00](https://github.com/opencadc/canfar/commit/6efed008e292c557cbf44f7f1c3ca2113f3d14af))
* **docs:** updated legacy docs with link fixes and moved around the toc ([662b9bd](https://github.com/opencadc/canfar/commit/662b9bdf68c4cf7b99fe6bb7b6b2f97841da3d16))
* **docs:** updated main page based on feedback ([96faabf](https://github.com/opencadc/canfar/commit/96faabfa711d2d254bf9a50192368412076de90b))
* **docs:** updated release notes and community reorg ([46b819a](https://github.com/opencadc/canfar/commit/46b819ae687eb4f3d18bbfbd4835c08dc84e4d3c))
* **docs:** updated test architecture docs ([4c32ef8](https://github.com/opencadc/canfar/commit/4c32ef8ee4ac7ddfdab5b5428c5b9748e8f7a460))
* **gha:** fix for gh-pages push ([27aa8f8](https://github.com/opencadc/canfar/commit/27aa8f816575d41b060aec947b8824ee5322f25b))
* **github-actions:** added fixes for release deployments ([dc1b03d](https://github.com/opencadc/canfar/commit/dc1b03d5151f9b839eceb0ff616004efc729fa38))
* **github-actions:** added path restrictions for workflow triggers, reduced permissions for build flows ([1220765](https://github.com/opencadc/canfar/commit/12207651d6f901ec4bd1820cfeb5f3cdf7edb0a1))
* **github-actions:** fix for disabling pypi release ([078176a](https://github.com/opencadc/canfar/commit/078176add980dd72ad168457e41a0258914ea4e3))
* **github-actions:** migrated worklows to be under opencadc/canfar ([0f267f5](https://github.com/opencadc/canfar/commit/0f267f5accd2fa42f8bba19a1aa1af2de8df84da))
* **github-actions:** possible fix for deployment action ([41e1886](https://github.com/opencadc/canfar/commit/41e1886e200a93f23b251259cf7b25192baa5445))
* **github-actions:** release actions now checkout tag_name ref for code ([ebffafe](https://github.com/opencadc/canfar/commit/ebffafe6d11149d8fc05b9a4787dce16923f9c76))
* **httpx:** updated httpx hook and tests ([f0f24e5](https://github.com/opencadc/canfar/commit/f0f24e5d1bdf1d15a1bdefdb4f43d8e96486b41c))
* **httpx:** updated httpx hook and tests ([7a3621d](https://github.com/opencadc/canfar/commit/7a3621df72303985c1f4a2788dcc313895535762))
* Implement httpx error logging hooks and client integration ([fee71c2](https://github.com/opencadc/canfar/commit/fee71c287a7970cfad1f3db3cd1f12766f716fe1))
* **import:** fix for ruff TypeChecking import error ([6b5aa6f](https://github.com/opencadc/canfar/commit/6b5aa6f396837714be37afd78cdf2bef53fb779f))
* **init:** added CERT_PATH as module global ([bb4642d](https://github.com/opencadc/canfar/commit/bb4642d434f532baa9f96c1acaa64f3f00105466))
* **lint:** major improvements to standards ([264b9b5](https://github.com/opencadc/canfar/commit/264b9b5b73bea1bee4e077004e8c6f6057c97556))
* **log:** fixed a missed f-string ([bf31015](https://github.com/opencadc/canfar/commit/bf31015a8f3e224eb46b576d8c03450cc821f735))
* **logging:** moved all modules to use the new logging facility ([e05399f](https://github.com/opencadc/canfar/commit/e05399fb848251aa0f309f14615236a833944559))
* **models:** added `Failed` as a status ([ef2c34e](https://github.com/opencadc/canfar/commit/ef2c34e8fafe084ad5a12d53d6b3a7d8538c14e3))
* **models:** added desktop-app and contributed to allowed kinds ([2b8514f](https://github.com/opencadc/canfar/commit/2b8514f432dccd7e971fa3401b53f20d270f07d0))
* **models:** added logging ([514fda2](https://github.com/opencadc/canfar/commit/514fda226a5167ed200b63f0e0bfab06901f4683))
* **models:** create.spec model used in session.create now expects env to be None by default ([c34b110](https://github.com/opencadc/canfar/commit/c34b110fba0e8a84d5e811bc55060fb7a370f6b5))
* **models:** CreateSpec ([f4cd04f](https://github.com/opencadc/canfar/commit/f4cd04fd83cd2fdd667a01f4d1fb086efa800825))
* **models:** createSpec model now outputs kind with alias type ([3184d5c](https://github.com/opencadc/canfar/commit/3184d5c8df740d04b652fa94282682de9084b8d3))
* **models:** fixes model import errors for pydantic ([fd264d4](https://github.com/opencadc/canfar/commit/fd264d410544b1896bc4857fec44f95c1f77b7f2))
* **models:** models no longer search for SKAHA_REGISTRY_[USERNAME|SECRET] from environ, this will be supported in future releases with a comprehensive environment variable support accross all configurable variables ([a1702c9](https://github.com/opencadc/canfar/commit/a1702c90c1b735ab329b7eedbdabc5811a0eb915))
* **models:** typo ([4c7dbe6](https://github.com/opencadc/canfar/commit/4c7dbe6159fb90b9e798a5b293a3877ac3855fe3))
* **models:** update server fields to allow None values and adjust default handling ([84b9c5d](https://github.com/opencadc/canfar/commit/84b9c5d982109a36de9f8ba0f383257c10aadeee))
* **models:** updated checks for session kind ([a8317f4](https://github.com/opencadc/canfar/commit/a8317f41fa7f59b50d9fb0f7b52bb0a1aafc117d))
* **models:** updated client auth and reg models ([b1c3f2b](https://github.com/opencadc/canfar/commit/b1c3f2bb3d923c62600eeae02e19f9a268fc646c))
* **models:** updated client config model for better backwards compatibility ([e10f007](https://github.com/opencadc/canfar/commit/e10f0079c036232bc108b970238754be59bbbf1a))
* **models:** x509 now does a lazy, rather than an eager check for cert path ([eb16f76](https://github.com/opencadc/canfar/commit/eb16f76b37d17b90963c87327e053e07dfd02058))
* **model:** updates to default config to add auth tracking offered by the upstream server ([52e291e](https://github.com/opencadc/canfar/commit/52e291ed8d3e57471e6180d7033d4524b71785ca))
* **mypy:** setting extra checks to true ([0a29305](https://github.com/opencadc/canfar/commit/0a29305d8ea88115db535c4655529b17e73f4f58))
* **oidc:** streamline OIDC imports and update token expiry handling ([ff0b62d](https://github.com/opencadc/canfar/commit/ff0b62d43ecdbbbff13b958da369b0ce6254ac4b))
* **overview:** baseurl fix ([4bcb8f4](https://github.com/opencadc/canfar/commit/4bcb8f4f4095790fe215c22b3389296d52f2fad6))
* **pre-commit:** add autofix argument to pretty-format-json hook ([fddeb54](https://github.com/opencadc/canfar/commit/fddeb549527b2fe161a3e4f7e9eedf33a3def8c4))
* **pre-commit:** added jwt to mypy ([f787507](https://github.com/opencadc/canfar/commit/f7875070c35f1cbbfda33b1d1716896524edf9b0))
* **pre-commit:** cleanup ([abb0839](https://github.com/opencadc/canfar/commit/abb083980a90018d244ce0e4a91ecc363597f2e4))
* **pre-commit:** updates ([fa1b1c4](https://github.com/opencadc/canfar/commit/fa1b1c49465899c3db08f1669b2a468905291b1f))
* **pyproject:** fixed toml file with bad license key ([ac1ffb6](https://github.com/opencadc/canfar/commit/ac1ffb620ae4fbfabcbd5c136f192d56949ba29b))
* **readme:** codeql bagde url ([197a6eb](https://github.com/opencadc/canfar/commit/197a6eb2ccbcb1451d5ce0fd15672e80dd9d87d6))
* **registry:** added keel-dev to discoverable registeries ([78ccbe6](https://github.com/opencadc/canfar/commit/78ccbe656fd1d6decd34ff625b46402a3c5fb6b3))
* **registry:** added swedish skaha server ([cfad0ef](https://github.com/opencadc/canfar/commit/cfad0ef49b076355b0491037fe3557d1aaace975))
* **registry:** fix for testing to include keel-dev ([dcf3cda](https://github.com/opencadc/canfar/commit/dcf3cdaa4177f5c48d9f908811d9841d4ad64367))
* **release-please:** reorder package-name and release-type fields for clarity, and autofix for json formatting ([fddeb54](https://github.com/opencadc/canfar/commit/fddeb549527b2fe161a3e4f7e9eedf33a3def8c4))
* remove image link ([a5c9766](https://github.com/opencadc/canfar/commit/a5c976603de755a13b6c950d9720c12807571b01))
* **security:** fixing logging of sensitive info ([07ff1d0](https://github.com/opencadc/canfar/commit/07ff1d0e26881b308673d4d181cfd0346eb27047))
* **security:** improvements to assertion checks ([2ea1108](https://github.com/opencadc/canfar/commit/2ea11088d2879918d653dd1c7bd8eaf2ceff24d6))
* **security:** private init ([0fada02](https://github.com/opencadc/canfar/commit/0fada023ce59c2a30001a9486964309616eb67b5))
* **security:** removed secret info ([dccb1c2](https://github.com/opencadc/canfar/commit/dccb1c241006109bc9cea6a7cea949854135915e))
* **security:** restricting ssl context to use TLSv1.2 at a minimum ([09654d0](https://github.com/opencadc/canfar/commit/09654d01d4fbd3092930fa82ef87d504ca4583c0))
* **security:** X509 certs are checked if valid before first conn. to server ([08327a9](https://github.com/opencadc/canfar/commit/08327a9ea233ed67084f5a1fd6347f919111aea5))
* **session:** events now returns None, when verbose=True ([1b01dd6](https://github.com/opencadc/canfar/commit/1b01dd6cfb5972d6476a297679f341e6b00e1bd2))
* **session:** fixed kind translation for session.create, increased max replicas limit to 512 ([9bfe357](https://github.com/opencadc/canfar/commit/9bfe3575fb78209df546886d08654874799c7b07))
* **session:** fixed set env in session.create ([00b67ac](https://github.com/opencadc/canfar/commit/00b67ac1c834439596e481e0a5db17c33f9d7290))
* **session:** fixed sync log output when verbose is True ([6ac63f9](https://github.com/opencadc/canfar/commit/6ac63f9e1a13d7c31d3e0626ae638bb40ed27650))
* **session:** improved docs, better testing logic to await async sleep ([e54b9af](https://github.com/opencadc/canfar/commit/e54b9af2e011692250e11efb1abf0be6ce53e40b))
* **session:** solidified the skaha async session api, moved common query building logic to utils.build ([3f11aee](https://github.com/opencadc/canfar/commit/3f11aeea5b8ea3617a7d6eed4b4d86863ce4f856))
* **skaha-client:** deprecated verify field ([a70c4b4](https://github.com/opencadc/canfar/commit/a70c4b494f1ef54bb78e0d0689034a2ed614217b))
* **style:** lint ([248565f](https://github.com/opencadc/canfar/commit/248565f2c48a4d1d220a2f4c5d302b812af5d422))
* **tests:** consolidated registry tests ([80ad530](https://github.com/opencadc/canfar/commit/80ad530646b89c39e67215e1728179035ec7a124))
* **tests:** ensure newline at end of file in test_servers_mixed_status ([b50349e](https://github.com/opencadc/canfar/commit/b50349eb03148ff00afc6ff8062a887c3b68eb16))
* **tests:** fix for comparing float values ([f391833](https://github.com/opencadc/canfar/commit/f3918331f67cba6d4fa57ad6aef85d5804433be4))
* **tests:** fix for stdout ([6c25d3e](https://github.com/opencadc/canfar/commit/6c25d3e816a969954fda46d7edf765627182d685))
* **tests:** fixed issue with session tests ([d004fde](https://github.com/opencadc/canfar/commit/d004fde6b9cf17cf49bac833151d2fc5945486d6))
* **tests:** fixed issues with codecov tokens ([07f87d9](https://github.com/opencadc/canfar/commit/07f87d984959501329dcca1e6ee7ed83f14c3f1a))
* **tests:** for bad filenames ([f0f4831](https://github.com/opencadc/canfar/commit/f0f483118dd97038ce811b6b0d6f846323c675ac))
* **tests:** import ([54ed5fc](https://github.com/opencadc/canfar/commit/54ed5fc492375a21292c556fb162542d90f5fc0f))
* **tests:** refactor authentication tests to use updated model attributes and improve structure ([8cfa73f](https://github.com/opencadc/canfar/commit/8cfa73ff536d8526c36474fe53a7032192d788b3))
* **tests:** removed not needed tests ([d5be89c](https://github.com/opencadc/canfar/commit/d5be89c87bbfdbc40f07237a91ff3cd3dddb1540))
* **tests:** removed now redundant test ([651793f](https://github.com/opencadc/canfar/commit/651793ff14ba6435310a06285d0beaf5498a96f8))
* **tests:** removed now redundant test ([c6b519c](https://github.com/opencadc/canfar/commit/c6b519c3beb31fa2b525fdf064ad4843a83aafa9))
* **tests:** stdout related errors ([e262eb3](https://github.com/opencadc/canfar/commit/e262eb3c7323180d67f8815995526cc9ca7347c4))
* **tests:** tmp filename ([1dd4477](https://github.com/opencadc/canfar/commit/1dd4477df330074d98645ce38fe4cedf05c317d6))
* **tests:** update mock path mkdir lambda to accept arbitrary arguments ([2939796](https://github.com/opencadc/canfar/commit/29397961baf9f0ac4d7640b488dd094349191738))
* **tests:** update URL validation tests to reject 'sftp' scheme ([9117701](https://github.com/opencadc/canfar/commit/9117701bfdf963ce2bf86f4bd0b107b3f026c737))
* **tests:** updates ([53a0a7e](https://github.com/opencadc/canfar/commit/53a0a7e461d1b64d130e968f0e8716c232519b8d))
* **utils:** crypto fix for generating funny names :D ([2eff101](https://github.com/opencadc/canfar/commit/2eff101998c927ce62fed6c414291a4af412e44a))
* **utils:** fixed logging x2 issue ([7e218df](https://github.com/opencadc/canfar/commit/7e218df82d7b97087a84ad8ea0ee621a029363e3))
* **utils:** vosi ([c925e5a](https://github.com/opencadc/canfar/commit/c925e5ae3b0019f5249a6b09b97d455215030475))
* **wip:** lint/style/type-hinting ([ced042d](https://github.com/opencadc/canfar/commit/ced042d425d657bbfb1e7375305aebdd304cb855))
* **x509:** fixes for handling unintialized expiry ([76e7523](https://github.com/opencadc/canfar/commit/76e7523344d903c72e4db272d11c1ad526769312))
* **x509:** updated x509 auth utils to be all colocated and updated tests ([9e5e7c6](https://github.com/opencadc/canfar/commit/9e5e7c6553389ac96d8eb018472c189ef60dc4f9))


### Documentation

* add CanfarSP 2025.1 release notes to homepage ([86b1a32](https://github.com/opencadc/canfar/commit/86b1a328f33b04ce91dedd578e42222199e1d5af))
* add detailed technical information and links to release notes ([003b8a5](https://github.com/opencadc/canfar/commit/003b8a5b16c430c065e27487230282d833834f2c))
* **api:** added better explanation for flexible mode resources ([a153418](https://github.com/opencadc/canfar/commit/a1534180307d26b2c2c6378ae51f7847d9068294))
* **asyncSession:** added docs ([a8be7fc](https://github.com/opencadc/canfar/commit/a8be7fc540c35f85d24b16f233ef46107302ac5a))
* **auth:** added auth and context docs ([65d3c2e](https://github.com/opencadc/canfar/commit/65d3c2ef5dcd3150c5aec07f5b801cb530272c9b))
* **bug-reports:** added issue template and docs for reporting bugs ([1e177ea](https://github.com/opencadc/canfar/commit/1e177ea5eee695a103d6b359f38d90626d1166a0))
* **cleanup:** links and repeated flexible session info ([3080f11](https://github.com/opencadc/canfar/commit/3080f117e2af7720c6714f1d63e1706cdb417429))
* **cli:** added docs ([9a7f20a](https://github.com/opencadc/canfar/commit/9a7f20a5b9b48608d246047692bcf3309ed947fd))
* **client:** updated class docstring ([5531c6f](https://github.com/opencadc/canfar/commit/5531c6f3794312a1fac64ffbed2f4e20033803c2))
* **client:** updated client documentation ([74e64ec](https://github.com/opencadc/canfar/commit/74e64ec5d8bf92a9f1a9eeacf75e2ed11526b890))
* **client:** updates ([3db735b](https://github.com/opencadc/canfar/commit/3db735b8f4b94e9f0dccfc6717c68e6ebf6fdee1))
* Complete documentation cleanup and integration ([c36a599](https://github.com/opencadc/canfar/commit/c36a5998e7335c3d2bc162a80ceaa9a3d677971f))
* comprehensive review and updates across user guide sections ([0e503c0](https://github.com/opencadc/canfar/commit/0e503c0312fbf44235dc1cdd23993e73bfcac5e6))
* **contributing:** add note on alternative tooling for dependency management ([f7683db](https://github.com/opencadc/canfar/commit/f7683db3d5886bdee25bf33aade192ae797f63c5))
* **css:** updated canfar logo ([7bdbd75](https://github.com/opencadc/canfar/commit/7bdbd75fc86c0141ab6c1a702dde2da687b33779))
* **doi:** updated formatting of the doi details section ([6133c1a](https://github.com/opencadc/canfar/commit/6133c1a3338bf4ad2e0aaf4c991a9a378992ec10))
* **events:** added session.events docs ([7540062](https://github.com/opencadc/canfar/commit/7540062a53f480555c8e38253a34d2dd6c8484db))
* **flexible:** added docs for flexible session support in cli, client and concepts ([dfbdf1d](https://github.com/opencadc/canfar/commit/dfbdf1d10a336806719cc0f2a8b35f86f128c13b))
* **github-actions:** changed the workflow name ([868e114](https://github.com/opencadc/canfar/commit/868e1147e7a32c69d92cc325db7b3074feeace31))
* **helpers:** updated docs for distributed.chunk and distributed.stripe usage ([a8c15a0](https://github.com/opencadc/canfar/commit/a8c15a087cbc601bdebbceb311d0216a1976cb06))
* **helpers:** updated docs to be better for advanced examples ([4eb7558](https://github.com/opencadc/canfar/commit/4eb7558f297b57a1d1ba2e2dee62432e3acd2ef6))
* **hyperlinks:** fixed after docs reorg ([4301283](https://github.com/opencadc/canfar/commit/43012839248851b0e1e591c7d28f81f3db29a3ee))
* **index:** typo fixes ([bc637c5](https://github.com/opencadc/canfar/commit/bc637c5b0e8e05b17d768e8a7cb7b9fb9dd766ab))
* **index:** updated the landing page ([e7dbac2](https://github.com/opencadc/canfar/commit/e7dbac2049e4bc9e24886c83d1d971c04119c0a8))
* **index:** updates ([a3c2e2e](https://github.com/opencadc/canfar/commit/a3c2e2e12a9d6311f0a7541c2293749df52138bc))
* **landing-page:** added publications and moved some things to footnotes ([6f09786](https://github.com/opencadc/canfar/commit/6f097865f773cb93554feedd81b87343e8c32034))
* **landing-page:** added publications and moved some things to footnotes ([afc2336](https://github.com/opencadc/canfar/commit/afc2336d576b05116540958e73a0199d2755b612))
* **landing-page:** clean up ([8ac0080](https://github.com/opencadc/canfar/commit/8ac0080238780fac9bc01c775b76ce1cf6b9e1f9))
* **landing-page:** cleanup and dyamic links ([41f5aef](https://github.com/opencadc/canfar/commit/41f5aeffa596884c7f360409d989b200506a01b8))
* **landing-page:** cleanup and dyamic links ([f37887b](https://github.com/opencadc/canfar/commit/f37887be9ece7da256b6bd7a0843ff068ef335ac))
* **pacakge:** major updates for docs, merged in science container docs ([3b9c12a](https://github.com/opencadc/canfar/commit/3b9c12ac3861aba5441ef7402cb0500a51acd983))
* **release-notes:** CSP 2025.1 ([d3ed86a](https://github.com/opencadc/canfar/commit/d3ed86a0ac1b4f78889ee494fc747c936304e564))
* **release-notes:** fixes ([627ee43](https://github.com/opencadc/canfar/commit/627ee43983cbd7a8bbdeec47cbdfe6a6a5d3afe8))
* **session:** docstring ([7189052](https://github.com/opencadc/canfar/commit/7189052f0727ed5937072bb56d6942bf54583fd3))
* **sessions:** added docs for destroy_with fucntionality ([afd0a11](https://github.com/opencadc/canfar/commit/afd0a1115dfd10535aa9cee9decda22136f6f10f))
* **sessions:** consolidate and add session images for notebook, carta, firefly, desktop, transfer_file; fix image paths ([a22d435](https://github.com/opencadc/canfar/commit/a22d4351add12d18f4e3ea3767600d0f079b7631))
* **session:** updated docs for session and async sessions ([7e49fef](https://github.com/opencadc/canfar/commit/7e49fef963dd536b2592b73b9c8d091cf0668984))
* **skaha:** update ([e40bad4](https://github.com/opencadc/canfar/commit/e40bad403b82e743acaf35b53d5180139241b47c))
* small text chagne ([835dc6c](https://github.com/opencadc/canfar/commit/835dc6ca66498daa620e62f25bebc672864c8e2e))
* **style:** updates ([e886d77](https://github.com/opencadc/canfar/commit/e886d77253d9b52f43bd5ab3d4c826b1d8a591c3))
* **tests:** updated info about slow tests ([a4401a3](https://github.com/opencadc/canfar/commit/a4401a3ef7680f5b23ddc9bc7a0a8ce6dda156e2))
* update for new registry authentication ([683d6b6](https://github.com/opencadc/canfar/commit/683d6b6ee543fe0a2630e8473cf3e6096a6421bc))
* **updates:** all over, work-in-progress ([8ea1cce](https://github.com/opencadc/canfar/commit/8ea1cced8474ed2be7f6ea92552f306a7cc4a18f))
* **updates:** docs ([c61fecd](https://github.com/opencadc/canfar/commit/c61fecd574dc0db2e7a8b36120b5539416b6bdbe))
* **updates:** site config + token support ([54d6ed9](https://github.com/opencadc/canfar/commit/54d6ed92285a44421450e1139d5f22e62c863694))
* **user-guides----documentations:** add legacy index and pages; update guides link; ([0867c96](https://github.com/opencadc/canfar/commit/0867c9620692967224428e01d8afe2eb5389b881))

## [0.8.0](https://github.com/opencadc/canfar/compare/v0.7.0...v0.8.0) (2025-08-08)


### Features

* **auth:** add HTTPx authentication hooks for token refresh ([489066d](https://github.com/opencadc/canfar/commit/489066d560d883f1bad77521e6fa5a02e754b494))
* **auth:** add OIDC authentication hooks for automatic token refresh ([bc4596f](https://github.com/opencadc/canfar/commit/bc4596fdad62db016a7cc81f00150a5fd2e85150))
* **auth:** added oidc device flow logic ([1013cf5](https://github.com/opencadc/canfar/commit/1013cf551dceaafeeed25a2e1fdd11a8c375c9d5))
* **auth:** added x509 cert get logic ([657a97d](https://github.com/opencadc/canfar/commit/657a97de3c455e8ab26c1eb84a4dd794f4ebd5eb))
* **auth:** implement async and sync OIDC token refresh functions ([b43b05f](https://github.com/opencadc/canfar/commit/b43b05f60c70c8c95d2b4e9e6052df44b2e35d59))
* **auth:** server info is now saved for each auth config ([1788c1e](https://github.com/opencadc/canfar/commit/1788c1e35a93142b47a20c2d71c5f8609a40d05b))
* **cli:** added `skaha open` command to open sessions in a web browser. Made skaha info more readable ([c932187](https://github.com/opencadc/canfar/commit/c932187838c8c2f2a544dbde396ea79b484b661e))
* **cli:** added auth cmds: list, switch, rm & purge ([6ab0bd8](https://github.com/opencadc/canfar/commit/6ab0bd8c15c14fdbd5ada3c75bf68af022e7c186))
* **cli:** added entrypoing cf ([cf3fce8](https://github.com/opencadc/canfar/commit/cf3fce8dc49fc7c763bab218dd896a0ff22bb414))
* **cli:** added feat to auto discover skaha servers ([46eb565](https://github.com/opencadc/canfar/commit/46eb565e00e3bf4ff95020d87f15a93d64f16d4a))
* **cli:** added list, ls to skaha ps as aliases ([c88eb6a](https://github.com/opencadc/canfar/commit/c88eb6ab7369dd88a3e7b27e58a9c751f403e917))
* **cli:** added support for using the CLI as canfar ([5051af1](https://github.com/opencadc/canfar/commit/5051af190e188d2231d9aea98056b52d2eb65725))
* **client:** add expiry property and enhance SSL context handling for authentication ([cb6261a](https://github.com/opencadc/canfar/commit/cb6261aaad67126c32ac350de42777ea8ae21d6f))
* **client:** enhance SkahaClient documentation and improve authentication handling ([1e6b770](https://github.com/opencadc/canfar/commit/1e6b7708d009a207ccf60ee8aaa233df26f8ef97))
* **client:** significant improvements to the base skaha client to support context managers ([a197553](https://github.com/opencadc/canfar/commit/a19755376984a338e8ea56d73f9bec71463c7a34))
* **cli:** work-in-process ([2e646ab](https://github.com/opencadc/canfar/commit/2e646ab2586701f908d78844f94a3bc41b0c6a65))
* **config:** updated auth config to provide valid & expired checks for all auth types and added tests ([4dc6929](https://github.com/opencadc/canfar/commit/4dc6929b7538d3a230a9c1d4c3a134ec9835ec7c))
* **discover:** added functionality to discover skaha servers from registries and also added tests ([5857772](https://github.com/opencadc/canfar/commit/5857772563d354ad0ad5a90c0620b4689f904b54))
* **exceptions:** added skaha exception classes ([0651191](https://github.com/opencadc/canfar/commit/0651191ace890b489af64af6cd49cd892871fe38))
* **garble:** added fernet and rot13 ciphers to encrypt/obsfucate sensitive info ([7204879](https://github.com/opencadc/canfar/commit/72048791e297c46cd4a2d738ae4a25dc545348ff))
* **helpers:** added code to to split tasks for large scale processing ([6ffe5cb](https://github.com/opencadc/canfar/commit/6ffe5cb3328628f3782477d2927b2b458e477bc8))
* **hooks:** added cli tool typer hook for multiple command aliases ([6c5bc15](https://github.com/opencadc/canfar/commit/6c5bc150f969bf49edd14273a4aaef80f31fa57b))
* **logging:** added comprehensive rich based logger for the project ([a48c520](https://github.com/opencadc/canfar/commit/a48c520390db965825a0053722789cdb31812dab))
* **models:** added http models for the client ([0679e8f](https://github.com/opencadc/canfar/commit/0679e8f86055f01a4e54b4c63fe8e77ddc8d88b6))
* **models:** all client models have been moved to skaha.models ([a07c676](https://github.com/opencadc/canfar/commit/a07c6760ff824a6dcc647a67be2a9abcc27cf52d))
* **oidc:** added tests and made the oidc auth flow async ([0059e12](https://github.com/opencadc/canfar/commit/0059e128015e737ec3f008bf01afb5aa2b667392))
* **tests:** add comprehensive tests for OIDC authentication and HTTPx hooks ([be7fb50](https://github.com/opencadc/canfar/commit/be7fb505127cfa2496a852316e3601520cc27d37))
* **types:** added mode, which reflects the auth type of the client ([5781e4a](https://github.com/opencadc/canfar/commit/5781e4ad2c39be0faea78a6a814bb58c0d8cec79))
* **types:** updated to the auth data model ([7f293c4](https://github.com/opencadc/canfar/commit/7f293c43a1a028be38a27787a44f1d781580acc7))


### Bug Fixes

* **auth, config, http:** refactor imports and clean up default handling in models ([6095a09](https://github.com/opencadc/canfar/commit/6095a09b3a94a01ac509dc3f8b9937c5d754c472))
* **auth, config, models:** refactor authentication handling and improve configuration properties ([aaa8c61](https://github.com/opencadc/canfar/commit/aaa8c618dd4c9de6314437a170e33d5f63328ced))
* **auth:** added comprehensive login support ([bd11fe4](https://github.com/opencadc/canfar/commit/bd11fe4f27e473a7461112d4f9e881bf6858dbb7))
* **auth:** improve login flow and server selection logic ([18b8d6d](https://github.com/opencadc/canfar/commit/18b8d6d881e5d70b9ee9f728a982ba13034b8fe6))
* **auth:** x509 expired now return True when there is no cert to be found ([2ab7141](https://github.com/opencadc/canfar/commit/2ab71416106aa107d06c773e3af641eba387f95d))
* **auth:** x509 now has better exception handling ([a4469b3](https://github.com/opencadc/canfar/commit/a4469b3282fc32c3bc2e4dae5fd11e8dda89c3c3))
* **cli:** added a new aliases section to cleanup the l&f of the cli ([6165575](https://github.com/opencadc/canfar/commit/6165575887826b0acf8dc8e2f59f21b08e946606))
* **cli:** added new aliases for list and create, fixed added `Terminating` state for Status models ([a7e946d](https://github.com/opencadc/canfar/commit/a7e946de8730a23609439bdb52a227ae576eaafa)), closes [#103](https://github.com/opencadc/canfar/issues/103)
* **cli:** config - added path ([30f2617](https://github.com/opencadc/canfar/commit/30f26178f8ead4286f14dbcc77095d9323198e7b))
* **cli:** create options cpus changed to cpu ([05081ed](https://github.com/opencadc/canfar/commit/05081ed6b528e0688f5a42a1fa514672cea7582b))
* **client, overview:** refactor base URL handling to use 'url' attribute instead of 'server' ([b429820](https://github.com/opencadc/canfar/commit/b429820807398c55b9b83f128a79f51f893d9c64))
* **client:** the skaha client on performs x509 checks when creating the clients ([b6c3b80](https://github.com/opencadc/canfar/commit/b6c3b80fa84d990995496aa695bc7ad7d51f875b))
* **cli:** fix for stats output print statement ([856df95](https://github.com/opencadc/canfar/commit/856df95171ae433bc5a5d6759a59d7ccc2a549b2))
* **cli:** numerous fixes for general look and feel, updated usage and help to be more descriptive ([ea59085](https://github.com/opencadc/canfar/commit/ea59085b359d040cc219d5e76680b354d9ad593b))
* **cli:** ps,list,ls are now sorted by startTime ([fdf34ed](https://github.com/opencadc/canfar/commit/fdf34edc957545cf2f74eb4887b51b7099a38f2d))
* **cli:** updated the discover logic to be cleaner ([ebff177](https://github.com/opencadc/canfar/commit/ebff177eab097de019cc13bb7876abf59b850762))
* **docs:** improve docstrings for clarity and consistency across authentication modules ([48599d3](https://github.com/opencadc/canfar/commit/48599d3dd683d68af242b433e339a2018f382f93))
* **docs:** improve formatting of docstring for gather function parameters ([9807194](https://github.com/opencadc/canfar/commit/980719411abdcc2c67df00dd6ca3419e0f822424))
* **docs:** remove slow tests details and clarify slow test marking criteria ([18999b7](https://github.com/opencadc/canfar/commit/18999b74bf652eb6eefbd4887b9128854db15250))
* **docs:** updated test architecture docs ([4c32ef8](https://github.com/opencadc/canfar/commit/4c32ef8ee4ac7ddfdab5b5428c5b9748e8f7a460))
* **github-actions:** fix for disabling pypi release ([078176a](https://github.com/opencadc/canfar/commit/078176add980dd72ad168457e41a0258914ea4e3))
* **github-actions:** migrated worklows to be under opencadc/canfar ([0f267f5](https://github.com/opencadc/canfar/commit/0f267f5accd2fa42f8bba19a1aa1af2de8df84da))
* **import:** fix for ruff TypeChecking import error ([6b5aa6f](https://github.com/opencadc/canfar/commit/6b5aa6f396837714be37afd78cdf2bef53fb779f))
* **init:** added CERT_PATH as module global ([bb4642d](https://github.com/opencadc/canfar/commit/bb4642d434f532baa9f96c1acaa64f3f00105466))
* **lint:** major improvements to standards ([264b9b5](https://github.com/opencadc/canfar/commit/264b9b5b73bea1bee4e077004e8c6f6057c97556))
* **log:** fixed a missed f-string ([bf31015](https://github.com/opencadc/canfar/commit/bf31015a8f3e224eb46b576d8c03450cc821f735))
* **logging:** moved all modules to use the new logging facility ([e05399f](https://github.com/opencadc/canfar/commit/e05399fb848251aa0f309f14615236a833944559))
* **models:** added `Failed` as a status ([ef2c34e](https://github.com/opencadc/canfar/commit/ef2c34e8fafe084ad5a12d53d6b3a7d8538c14e3))
* **models:** added desktop-app and contributed to allowed kinds ([2b8514f](https://github.com/opencadc/canfar/commit/2b8514f432dccd7e971fa3401b53f20d270f07d0))
* **models:** CreateSpec ([f4cd04f](https://github.com/opencadc/canfar/commit/f4cd04fd83cd2fdd667a01f4d1fb086efa800825))
* **models:** fixes model import errors for pydantic ([fd264d4](https://github.com/opencadc/canfar/commit/fd264d410544b1896bc4857fec44f95c1f77b7f2))
* **models:** typo ([4c7dbe6](https://github.com/opencadc/canfar/commit/4c7dbe6159fb90b9e798a5b293a3877ac3855fe3))
* **models:** update server fields to allow None values and adjust default handling ([84b9c5d](https://github.com/opencadc/canfar/commit/84b9c5d982109a36de9f8ba0f383257c10aadeee))
* **models:** updated client auth and reg models ([b1c3f2b](https://github.com/opencadc/canfar/commit/b1c3f2bb3d923c62600eeae02e19f9a268fc646c))
* **models:** updated client config model for better backwards compatibility ([e10f007](https://github.com/opencadc/canfar/commit/e10f0079c036232bc108b970238754be59bbbf1a))
* **models:** x509 now does a lazy, rather than an eager check for cert path ([eb16f76](https://github.com/opencadc/canfar/commit/eb16f76b37d17b90963c87327e053e07dfd02058))
* **mypy:** setting extra checks to true ([0a29305](https://github.com/opencadc/canfar/commit/0a29305d8ea88115db535c4655529b17e73f4f58))
* **oidc:** streamline OIDC imports and update token expiry handling ([ff0b62d](https://github.com/opencadc/canfar/commit/ff0b62d43ecdbbbff13b958da369b0ce6254ac4b))
* **overview:** baseurl fix ([4bcb8f4](https://github.com/opencadc/canfar/commit/4bcb8f4f4095790fe215c22b3389296d52f2fad6))
* **pre-commit:** added jwt to mypy ([f787507](https://github.com/opencadc/canfar/commit/f7875070c35f1cbbfda33b1d1716896524edf9b0))
* **pre-commit:** updates ([fa1b1c4](https://github.com/opencadc/canfar/commit/fa1b1c49465899c3db08f1669b2a468905291b1f))
* **registry:** added swedish skaha server ([cfad0ef](https://github.com/opencadc/canfar/commit/cfad0ef49b076355b0491037fe3557d1aaace975))
* **security:** fixing logging of sensitive info ([07ff1d0](https://github.com/opencadc/canfar/commit/07ff1d0e26881b308673d4d181cfd0346eb27047))
* **security:** private init ([0fada02](https://github.com/opencadc/canfar/commit/0fada023ce59c2a30001a9486964309616eb67b5))
* **security:** removed secret info ([dccb1c2](https://github.com/opencadc/canfar/commit/dccb1c241006109bc9cea6a7cea949854135915e))
* **skaha-client:** deprecated verify field ([a70c4b4](https://github.com/opencadc/canfar/commit/a70c4b494f1ef54bb78e0d0689034a2ed614217b))
* **style:** lint ([248565f](https://github.com/opencadc/canfar/commit/248565f2c48a4d1d220a2f4c5d302b812af5d422))
* **tests:** consolidated registry tests ([80ad530](https://github.com/opencadc/canfar/commit/80ad530646b89c39e67215e1728179035ec7a124))
* **tests:** ensure newline at end of file in test_servers_mixed_status ([b50349e](https://github.com/opencadc/canfar/commit/b50349eb03148ff00afc6ff8062a887c3b68eb16))
* **tests:** fix for comparing float values ([f391833](https://github.com/opencadc/canfar/commit/f3918331f67cba6d4fa57ad6aef85d5804433be4))
* **tests:** fix for stdout ([6c25d3e](https://github.com/opencadc/canfar/commit/6c25d3e816a969954fda46d7edf765627182d685))
* **tests:** for bad filenames ([f0f4831](https://github.com/opencadc/canfar/commit/f0f483118dd97038ce811b6b0d6f846323c675ac))
* **tests:** import ([54ed5fc](https://github.com/opencadc/canfar/commit/54ed5fc492375a21292c556fb162542d90f5fc0f))
* **tests:** refactor authentication tests to use updated model attributes and improve structure ([8cfa73f](https://github.com/opencadc/canfar/commit/8cfa73ff536d8526c36474fe53a7032192d788b3))
* **tests:** removed not needed tests ([d5be89c](https://github.com/opencadc/canfar/commit/d5be89c87bbfdbc40f07237a91ff3cd3dddb1540))
* **tests:** stdout related errors ([e262eb3](https://github.com/opencadc/canfar/commit/e262eb3c7323180d67f8815995526cc9ca7347c4))
* **tests:** tmp filename ([1dd4477](https://github.com/opencadc/canfar/commit/1dd4477df330074d98645ce38fe4cedf05c317d6))
* **tests:** update mock path mkdir lambda to accept arbitrary arguments ([2939796](https://github.com/opencadc/canfar/commit/29397961baf9f0ac4d7640b488dd094349191738))
* **tests:** update URL validation tests to reject 'sftp' scheme ([9117701](https://github.com/opencadc/canfar/commit/9117701bfdf963ce2bf86f4bd0b107b3f026c737))
* **tests:** updates ([53a0a7e](https://github.com/opencadc/canfar/commit/53a0a7e461d1b64d130e968f0e8716c232519b8d))
* **utils:** crypto fix for generating funny names :D ([2eff101](https://github.com/opencadc/canfar/commit/2eff101998c927ce62fed6c414291a4af412e44a))
* **wip:** lint/style/type-hinting ([ced042d](https://github.com/opencadc/canfar/commit/ced042d425d657bbfb1e7375305aebdd304cb855))
* **x509:** fixes for handling unintialized expiry ([76e7523](https://github.com/opencadc/canfar/commit/76e7523344d903c72e4db272d11c1ad526769312))
* **x509:** updated x509 auth utils to be all colocated and updated tests ([9e5e7c6](https://github.com/opencadc/canfar/commit/9e5e7c6553389ac96d8eb018472c189ef60dc4f9))


### Documentation

* **auth:** added auth and context docs ([65d3c2e](https://github.com/opencadc/canfar/commit/65d3c2ef5dcd3150c5aec07f5b801cb530272c9b))
* **bug-reports:** added issue template and docs for reporting bugs ([1e177ea](https://github.com/opencadc/canfar/commit/1e177ea5eee695a103d6b359f38d90626d1166a0))
* **cli:** added docs ([9a7f20a](https://github.com/opencadc/canfar/commit/9a7f20a5b9b48608d246047692bcf3309ed947fd))
* **client:** updates ([3db735b](https://github.com/opencadc/canfar/commit/3db735b8f4b94e9f0dccfc6717c68e6ebf6fdee1))
* **contributing:** add note on alternative tooling for dependency management ([f7683db](https://github.com/opencadc/canfar/commit/f7683db3d5886bdee25bf33aade192ae797f63c5))
* **helpers:** updated docs for distributed.chunk and distributed.stripe usage ([a8c15a0](https://github.com/opencadc/canfar/commit/a8c15a087cbc601bdebbceb311d0216a1976cb06))
* **helpers:** updated docs to be better for advanced examples ([4eb7558](https://github.com/opencadc/canfar/commit/4eb7558f297b57a1d1ba2e2dee62432e3acd2ef6))
* **skaha:** update ([e40bad4](https://github.com/opencadc/canfar/commit/e40bad403b82e743acaf35b53d5180139241b47c))
* **tests:** updated info about slow tests ([a4401a3](https://github.com/opencadc/canfar/commit/a4401a3ef7680f5b23ddc9bc7a0a8ce6dda156e2))
* **updates:** all over, work-in-progress ([8ea1cce](https://github.com/opencadc/canfar/commit/8ea1cced8474ed2be7f6ea92552f306a7cc4a18f))

## [0.7.0](https://github.com/opencadc/canfar/compare/v0.6.1...v0.7.0) (2025-05-28)


### Features

* **session:** added session.events to show deployment events on the cluster, e.g. loading container image etc ([58e9bca](https://github.com/opencadc/canfar/commit/58e9bca90652ffcbcca8eeaecf351123254d62c0))


### Bug Fixes

* **security:** improvements to assertion checks ([2ea1108](https://github.com/opencadc/canfar/commit/2ea11088d2879918d653dd1c7bd8eaf2ceff24d6))
* **security:** X509 certs are checked if valid before first conn. to server ([08327a9](https://github.com/opencadc/canfar/commit/08327a9ea233ed67084f5a1fd6347f919111aea5))
* **session:** events now returns None, when verbose=True ([1b01dd6](https://github.com/opencadc/canfar/commit/1b01dd6cfb5972d6476a297679f341e6b00e1bd2))
* **session:** improved docs, better testing logic to await async sleep ([e54b9af](https://github.com/opencadc/canfar/commit/e54b9af2e011692250e11efb1abf0be6ce53e40b))


### Documentation

* **events:** added session.events docs ([7540062](https://github.com/opencadc/canfar/commit/7540062a53f480555c8e38253a34d2dd6c8484db))
* **session:** docstring ([7189052](https://github.com/opencadc/canfar/commit/7189052f0727ed5937072bb56d6942bf54583fd3))

## [0.6.1](https://github.com/opencadc/canfar/compare/v0.6.0...v0.6.1) (2025-05-22)


### Bug Fixes

* **cleanup:** comments ([8a1a078](https://github.com/opencadc/canfar/commit/8a1a0785232c404b5b0b68cbd4b8b0349d09a34c))
* **gha:** fix for gh-pages push ([27aa8f8](https://github.com/opencadc/canfar/commit/27aa8f816575d41b060aec947b8824ee5322f25b))
* Implement httpx error logging hooks and client integration ([fee71c2](https://github.com/opencadc/canfar/commit/fee71c287a7970cfad1f3db3cd1f12766f716fe1))
* **pre-commit:** cleanup ([abb0839](https://github.com/opencadc/canfar/commit/abb083980a90018d244ce0e4a91ecc363597f2e4))
* **security:** restricting ssl context to use TLSv1.2 at a minimum ([09654d0](https://github.com/opencadc/canfar/commit/09654d01d4fbd3092930fa82ef87d504ca4583c0))

## [0.6.0](https://github.com/opencadc/canfar/compare/v0.5.2...v0.6.0) (2025-05-12)


### Features

* **client:** added loglevel to configure the python logging levels ([431f46d](https://github.com/opencadc/canfar/commit/431f46dd4abebff53edb1485a5d5064ef432f3bf))
* **client:** added token support to skaha client ([6c7c748](https://github.com/opencadc/canfar/commit/6c7c7486b6a078a77b5a6b42e2c8162d95ff80f7))
* **client:** updated skaha client to use httpx instead of requests ([4c10de8](https://github.com/opencadc/canfar/commit/4c10de87451e9687fe29c17f363e5736b36e8203))
* **logs:** added stdout for printing logs in terminal ([0c34cad](https://github.com/opencadc/canfar/commit/0c34cada7fee945d710727222b27e17e7d46bd06))
* **sessions:** added skaha AsyncSession ([2693272](https://github.com/opencadc/canfar/commit/26932724e4533bf1823cfad97e3b9ccc8ef5fd7b))
* **sessions:** added support for firefly ([87d16c1](https://github.com/opencadc/canfar/commit/87d16c1637d5848fbc522c3340c611df40f6d2fa))


### Bug Fixes

* **api:** updated context, images, overview with httpx ([391e857](https://github.com/opencadc/canfar/commit/391e85732dc324b1d2dee51c4d46d558e5d7d72f))
* **client:** changed to the default and max values of parallel conns ([ce552bf](https://github.com/opencadc/canfar/commit/ce552bff74602c3525154a5ef4308d9291e9cc53))
* **client:** deprecated client.verify since it no longer affects any logic ([9eed6e9](https://github.com/opencadc/canfar/commit/9eed6e95db5eadc45ed084bde5eab1cdab7ca727))
* **client:** fixed annotation issues for client, asyncClient ([889a6a8](https://github.com/opencadc/canfar/commit/889a6a8f9072cf663c10d648248e0a2928ba8873))
* **models:** models no longer search for SKAHA_REGISTRY_[USERNAME|SECRET] from environ, this will be supported in future releases with a comprehensive environment variable support accross all configurable variables ([a1702c9](https://github.com/opencadc/canfar/commit/a1702c90c1b735ab329b7eedbdabc5811a0eb915))
* **models:** updated checks for session kind ([a8317f4](https://github.com/opencadc/canfar/commit/a8317f41fa7f59b50d9fb0f7b52bb0a1aafc117d))
* **session:** fixed sync log output when verbose is True ([6ac63f9](https://github.com/opencadc/canfar/commit/6ac63f9e1a13d7c31d3e0626ae638bb40ed27650))
* **session:** solidified the skaha async session api, moved common query building logic to utils.build ([3f11aee](https://github.com/opencadc/canfar/commit/3f11aeea5b8ea3617a7d6eed4b4d86863ce4f856))


### Documentation

* **asyncSession:** added docs ([a8be7fc](https://github.com/opencadc/canfar/commit/a8be7fc540c35f85d24b16f233ef46107302ac5a))
* **client:** updated class docstring ([5531c6f](https://github.com/opencadc/canfar/commit/5531c6f3794312a1fac64ffbed2f4e20033803c2))
* **index:** typo fixes ([bc637c5](https://github.com/opencadc/canfar/commit/bc637c5b0e8e05b17d768e8a7cb7b9fb9dd766ab))
* **index:** updates ([a3c2e2e](https://github.com/opencadc/canfar/commit/a3c2e2e12a9d6311f0a7541c2293749df52138bc))
* **session:** updated docs for session and async sessions ([7e49fef](https://github.com/opencadc/canfar/commit/7e49fef963dd536b2592b73b9c8d091cf0668984))
* **updates:** docs ([c61fecd](https://github.com/opencadc/canfar/commit/c61fecd574dc0db2e7a8b36120b5539416b6bdbe))
* **updates:** site config + token support ([54d6ed9](https://github.com/opencadc/canfar/commit/54d6ed92285a44421450e1139d5f22e62c863694))

## [0.5.2](https://github.com/opencadc/canfar/compare/v0.5.1...v0.5.2) (2025-03-03)


### Bug Fixes

* **session:** fixed kind translation for session.create, increased max replicas limit to 512 ([9bfe357](https://github.com/opencadc/canfar/commit/9bfe3575fb78209df546886d08654874799c7b07))

## [0.5.1](https://github.com/opencadc/canfar/compare/v0.5.0...v0.5.1) (2025-02-26)


### Bug Fixes

* **models:** createSpec model now outputs kind with alias type ([3184d5c](https://github.com/opencadc/canfar/commit/3184d5c8df740d04b652fa94282682de9084b8d3))

## [0.5.0](https://github.com/opencadc/canfar/compare/v0.4.4...v0.5.0) (2024-11-22)


### Features

* **context:** updates to context.resources api ([4d08876](https://github.com/opencadc/canfar/commit/4d08876de0b49201ddef0b8c9ddc01f022fcf11f))


### Bug Fixes

* **docker:** fix for docker build due to uv path install changes ([00fd5de](https://github.com/opencadc/canfar/commit/00fd5de260793d00b33d65216058c94854e73133))


### Documentation

* **style:** updates ([e886d77](https://github.com/opencadc/canfar/commit/e886d77253d9b52f43bd5ab3d4c826b1d8a591c3))

## [0.4.4](https://github.com/opencadc/canfar/compare/v0.4.3...v0.4.4) (2024-11-22)


### Bug Fixes

* **session:** fixed set env in session.create ([00b67ac](https://github.com/opencadc/canfar/commit/00b67ac1c834439596e481e0a5db17c33f9d7290))

## [0.4.3](https://github.com/opencadc/canfar/compare/v0.4.2...v0.4.3) (2024-11-08)


### Bug Fixes

* **models:** create.spec model used in session.create now expects env to be None by default ([c34b110](https://github.com/opencadc/canfar/commit/c34b110fba0e8a84d5e811bc55060fb7a370f6b5))

## [0.4.2](https://github.com/opencadc/canfar/compare/v0.4.0...v0.4.2) (2024-10-30)


### Bug Fixes

* **models:** added logging ([514fda2](https://github.com/opencadc/canfar/commit/514fda226a5167ed200b63f0e0bfab06901f4683))


### Documentation

* **index:** updated the landing page ([e7dbac2](https://github.com/opencadc/canfar/commit/e7dbac2049e4bc9e24886c83d1d971c04119c0a8))

## [0.4.0](https://github.com/opencadc/canfar/commit/b68cefc0f9abf356fea1fdeb42034ba75b4bf42e) (2024-10-25)


### Features

* **build:** added edge container build and attestation ([d07e008](https://github.com/opencadc/canfar/commit/d07e008dd8c4de36a8e20ca50f5a91dc03f8afd4))
* **codecov:** added badge ([373412d](https://github.com/opencadc/canfar/commit/373412d8f8b6a806b111a5d8dac89c64a876d6b3))
* **conduct:** added a code of conduct for skaha community ([f37046e](https://github.com/opencadc/canfar/commit/f37046e4baab6fe83eb00a64e004772d89b8bea2))
* **contributions:** added a guideline ([271a6df](https://github.com/opencadc/canfar/commit/271a6df3a4d3417991488a3571181941be7ae9ce))
* **dockerfile:** added base dockerfile for the project ([28f7e51](https://github.com/opencadc/canfar/commit/28f7e5120d500081c44083f1141eeeacf89e1305))
* **docs:** added conduct,contributing,license and security sections to docs ([5cac3c0](https://github.com/opencadc/canfar/commit/5cac3c0d385564afd27b6d74dd139dd1162a8ae7))
* **github-actions:** added pypi release action and updated client payload ([b0b3593](https://github.com/opencadc/canfar/commit/b0b3593d7166559032de099cf829a96203126f78))
* **license:** project now uses the AGPLv3 license ([706f6f8](https://github.com/opencadc/canfar/commit/706f6f8afa0b649a316a7f77de08571fe22b0e8a))
* **module:** added support for private container registries ([3b47c5c](https://github.com/opencadc/canfar/commit/3b47c5cee4fb5838efb87b9d17a9f7cd6da3d629))
* **packaging:** moved skaha from poetry backend to uv ([3b7b89f](https://github.com/opencadc/canfar/commit/3b7b89fb508d261ea83df269349142be44089abd))
* **security:** added a security policy for the project ([1338e7f](https://github.com/opencadc/canfar/commit/1338e7fecb1855192c414a2ba80c02775a75b86b))
* **security:** ossf scorecard ([719cdfc](https://github.com/opencadc/canfar/commit/719cdfccb68f96eea509ae749cb9dd6fc7c0ba9e))
* **session:** added new feature to delete sessions with name prefix, kind and status ([056254b](https://github.com/opencadc/canfar/commit/056254b9143daa2721486b801093598f1dbc7baa)), closes [#37](https://github.com/opencadc/canfar/issues/37)
* **templates:** added bug report and feature requests templates ([8a8dd20](https://github.com/opencadc/canfar/commit/8a8dd205bebda814902f66cc39924b7280d817dc))
* **client:** updated client to include skaha version in prep for v1 release ([e6360c0](https://github.com/opencadc/canfar/commit/e6360c07d9b305463e00f2f8293e6c9a2dc83f42))
* **overview:** added new overview module ([4a6336f](https://github.com/opencadc/canfar/commit/4a6336ff9d1ff3e05701848a500d35585cb0b154))
* **docs:** added build ([9049b92](https://github.com/opencadc/canfar/commit/9049b92b211bf4081b07f397a1c62ce058f3183b))
* **session:** create session now embeds two env variables into the container, REPLICA_COUNT and REPLICA_ID ([ecbf48a](https://github.com/opencadc/canfar/commit/ecbf48ad19536945f2359e75d0c3482a2e77feee))
* **session:** added support for multiple session management ([219b74c](https://github.com/opencadc/canfar/commit/219b74cefc99264aca8f041a625dea30325c1f0d))
* **session:** skaha.sessions api deprecated ([e184663](https://github.com/opencadc/canfar/commit/e18466330e67a1b714da86062c79710fd459fa39))
* **release-please:** implemented ([2ac9728](https://github.com/opencadc/canfar/commit/2ac972870d84876a74c7631f8af5cad453fab81e))

### Bug Fixes

* **attestation:** added attestation for dockerhub container image ([0ff4ba2](https://github.com/opencadc/canfar/commit/0ff4ba2b321d61483325018d42f39c97d22eb3cb))
* **badge:** update to codeql bagde url ([c95b6e0](https://github.com/opencadc/canfar/commit/c95b6e075c8c81f079bca7936940da01645f04a7))
* **ci/cd:** bugfixes ([b4b153c](https://github.com/opencadc/canfar/commit/b4b153c5dbd92d127fb2ce6a6ac17bdf697b5cb7))
* **ci/cd:** fix for docs build ([98eea9b](https://github.com/opencadc/canfar/commit/98eea9b1c7a363fbfea4fef42a572af73df7f63d))
* **ci/cd:** fixes for action deprecations, and uv errors ([6a5af8c](https://github.com/opencadc/canfar/commit/6a5af8c5174f89f23ccd5ae490f0850761275f6f))
* **CI:** change to pre-commit checks ([6216b02](https://github.com/opencadc/canfar/commit/6216b0279b14e7d716e01f7f9782405ecb9244ca))
* **ci:** ci indent fix ([4e02f72](https://github.com/opencadc/canfar/commit/4e02f7258a51493fcaef6cf52817ce6799eb8cd7))
* **ci:** fix to edge container build ([59924bd](https://github.com/opencadc/canfar/commit/59924bd8193f609ec2e958eea59a333469d41de3))
* **ci:** improved secret cleanup ([990c5a1](https://github.com/opencadc/canfar/commit/990c5a1e461843db681417bb229bcb51c13d8aed))
* **contribution:** updated guidelines ([bc5400e](https://github.com/opencadc/canfar/commit/bc5400e9b2901d76a53c502d10688bf7f9361dfa))
* **dockerfile:** fix to stage names ([f46b081](https://github.com/opencadc/canfar/commit/f46b081dc6d9e7013e23f99e5e4e41e755dac81a))
* **docs/ci:** small fixes ([e92c9eb](https://github.com/opencadc/canfar/commit/e92c9eb004d3517a3f639b5c84fbc8eb8e7fa27c))
* **docs:** updated doc/status/badge links ([6efed00](https://github.com/opencadc/canfar/commit/6efed008e292c557cbf44f7f1c3ca2113f3d14af))
* **github-actions:** added fixes for release deployments ([dc1b03d](https://github.com/opencadc/canfar/commit/dc1b03d5151f9b839eceb0ff616004efc729fa38))
* **github-actions:** possible fix for deployment action ([41e1886](https://github.com/opencadc/canfar/commit/41e1886e200a93f23b251259cf7b25192baa5445))
* **github-actions:** release actions now checkout tag_name ref for code ([ebffafe](https://github.com/opencadc/canfar/commit/ebffafe6d11149d8fc05b9a4787dce16923f9c76))
* **readme:** codeql bagde url ([197a6eb](https://github.com/opencadc/canfar/commit/197a6eb2ccbcb1451d5ce0fd15672e80dd9d87d6))
* **tests:** debugging ci/cd and common errors ([7d6b3a9](https://github.com/opencadc/canfar/commit/7d6b3a979d0436acb4a9914d988f03e6a797b552))
* **tests:** fixed issue with session tests ([d004fde](https://github.com/opencadc/canfar/commit/d004fde6b9cf17cf49bac833151d2fc5945486d6))
* **tests:** fixed issues with codecov tokens ([07f87d9](https://github.com/opencadc/canfar/commit/07f87d984959501329dcca1e6ee7ed83f14c3f1a))
* **tests:** fixed session tests to be more consistent and run ~60s ([19f0a6e](https://github.com/opencadc/canfar/commit/19f0a6e00414bdd883ae699de1fb4edac5f5fba7))
* **tests:** fixed threading issue caused when one of the futures timesout ([ba55a38](https://github.com/opencadc/canfar/commit/ba55a380ab5f8bd9c06e34a9c6cf543ea4ec7923))
* **tests:** fixes for session tests ([b3f3e48](https://github.com/opencadc/canfar/commit/b3f3e4813953bc31e58c864f1f36f70a53bdac41))
* **typing:** multiple type hint fixes throughout the project ([a533481](https://github.com/opencadc/canfar/commit/a53348166f8573af8c9780ded4a08f0fe95d6e44))
* **utils:** fixed logging x2 issue ([7e218df](https://github.com/opencadc/canfar/commit/7e218df82d7b97087a84ad8ea0ee621a029363e3))
* **docs:** updated docs to include changelog, added reference for calling gpus in session.create ([e58f9be](https://github.com/opencadc/canfar/commit/e58f9be5ae07264bd8046d1980a742c4124d34a1))
* **deps:** updates ([5644e15](https://github.com/opencadc/canfar/commit/5644e15c5b28de2a54be2607d87ca2a3439e7659))
* **session:** fix for spawning sessions with gpus ([961f766](https://github.com/opencadc/canfar/commit/961f76673783f948a6cf0c3c2b70bb34e4d6d853))
* **tests:** fixed session tests, which now default spawn with name-{replica-id} format ([7e48031](https://github.com/opencadc/canfar/commit/7e48031281e5ed1e35b891655769977aa4d3fc44))
* **env:** fixed multiple tests and added support for multiple env parameters ([c0500bf](https://github.com/opencadc/canfar/commit/c0500bf9c49a359f0b45205a5d1d6524144940f1))
* **client:** updated session header to have the correct content-type ([3146e41](https://github.com/opencadc/canfar/commit/3146e418b6e075edcd5e34dd03e5b94879b17c08))
* **images:** images api now always prunes ([a436e21](https://github.com/opencadc/canfar/commit/a436e21085f00e5f6e5a408b1ff0bc486c6881f4))
* **pre-commit:** fixed broken pre-commit config ([baedb82](https://github.com/opencadc/canfar/commit/baedb825a63efca35573d064836b0928e2579029))
* **type-hints:** fixed broken hints ([9f4e9db](https://github.com/opencadc/canfar/commit/9f4e9dbba8a923d19e5e180f291c7ff216db9c64))
* **type-hints:** fixed broken type hints ([c1d1356](https://github.com/opencadc/canfar/commit/c1d1356bbba6642bb86e12b1aaf553094e83ea04))
* **gha:** fix to release action ([cc7b61a](https://github.com/opencadc/canfar/commit/cc7b61a472da50463f3159aac46f6aa3ae49e79c))

### Documentation

* **github-actions:** changed the workflow name ([868e114](https://github.com/opencadc/canfar/commit/868e1147e7a32c69d92cc325db7b3074feeace31))
* **README:** updated with CI status ([175ffce](https://github.com/opencadc/canfar/commit/175ffcecdeb6e89f45c078180b732f22890b6403))
* **sessions:** added docs for destroy_with fucntionality ([afd0a11](https://github.com/opencadc/canfar/commit/afd0a1115dfd10535aa9cee9decda22136f6f10f))
* **skaha:** updated all docs ([04551c9](https://github.com/opencadc/canfar/commit/04551c925320cc7bc068f554705975f2c429f4a5))
* **docs:** updates with a new ability to edit docs via PR ([aa2314d](https://github.com/opencadc/canfar/commit/aa2314d9f57778e7328f1c9f2fd64470a76af66b))
* **readme:** update ([1b975b6](https://github.com/opencadc/canfar/commit/1b975b67da82a68d8c5072cc5739dcd024f39584))
* **docs:** build command issue ([becbc60](https://github.com/opencadc/canfar/commit/becbc60fb605dd832a90b6b5e5941ce07dc092b6))
* **docs:** fixed build issue ([98b0543](https://github.com/opencadc/canfar/commit/98b0543f933087cac63955c40dd424285f70656f))
* **docs:** created documentation for the project ([e0f5483](https://github.com/opencadc/canfar/commit/e0f5483c2c72cd489258a84e3cb06d142a06f4da))
* **API:** changed where order of docs ([569d34f](https://github.com/opencadc/canfar/commit/569d34f00747fd1d2eff8f997ae277b63080df50))
