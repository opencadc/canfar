# Changelog

## [1.4.0](https://github.com/shinybrar/skaha/compare/v1.3.1...v1.4.0) (2024-10-22)


### Features

* **conduct:** added a code of conduct for skaha community ([f37046e](https://github.com/shinybrar/skaha/commit/f37046e4baab6fe83eb00a64e004772d89b8bea2))
* **contributions:** added a guideline ([271a6df](https://github.com/shinybrar/skaha/commit/271a6df3a4d3417991488a3571181941be7ae9ce))
* **docs:** added conduct,contributing,license and security sections to docs ([5cac3c0](https://github.com/shinybrar/skaha/commit/5cac3c0d385564afd27b6d74dd139dd1162a8ae7))
* **license:** project now uses the AGPLv3 license ([706f6f8](https://github.com/shinybrar/skaha/commit/706f6f8afa0b649a316a7f77de08571fe22b0e8a))
* **module:** added support for private container registries ([3b47c5c](https://github.com/shinybrar/skaha/commit/3b47c5cee4fb5838efb87b9d17a9f7cd6da3d629))
* **packaging:** moved skaha from poetry backend to uv ([3b7b89f](https://github.com/shinybrar/skaha/commit/3b7b89fb508d261ea83df269349142be44089abd))
* **security:** added a security policy for the project ([1338e7f](https://github.com/shinybrar/skaha/commit/1338e7fecb1855192c414a2ba80c02775a75b86b))
* **security:** ossf scorecard ([719cdfc](https://github.com/shinybrar/skaha/commit/719cdfccb68f96eea509ae749cb9dd6fc7c0ba9e))
* **templates:** added bug report and feature requests templates ([8a8dd20](https://github.com/shinybrar/skaha/commit/8a8dd205bebda814902f66cc39924b7280d817dc))


### Bug Fixes

* **ci/cd:** bugfixes ([b4b153c](https://github.com/shinybrar/skaha/commit/b4b153c5dbd92d127fb2ce6a6ac17bdf697b5cb7))
* **ci/cd:** fix for docs build ([98eea9b](https://github.com/shinybrar/skaha/commit/98eea9b1c7a363fbfea4fef42a572af73df7f63d))
* **ci/cd:** fixes for action deprecations, and uv errors ([6a5af8c](https://github.com/shinybrar/skaha/commit/6a5af8c5174f89f23ccd5ae490f0850761275f6f))
* **CI:** change to pre-commit checks ([6216b02](https://github.com/shinybrar/skaha/commit/6216b0279b14e7d716e01f7f9782405ecb9244ca))
* **ci:** ci indent fix ([4e02f72](https://github.com/shinybrar/skaha/commit/4e02f7258a51493fcaef6cf52817ce6799eb8cd7))
* **contribution:** updated guidelines ([bc5400e](https://github.com/shinybrar/skaha/commit/bc5400e9b2901d76a53c502d10688bf7f9361dfa))
* **docs/ci:** small fixes ([e92c9eb](https://github.com/shinybrar/skaha/commit/e92c9eb004d3517a3f639b5c84fbc8eb8e7fa27c))
* **docs:** updated doc/status/badge links ([6efed00](https://github.com/shinybrar/skaha/commit/6efed008e292c557cbf44f7f1c3ca2113f3d14af))
* **tests:** debugging ci/cd and common errors ([7d6b3a9](https://github.com/shinybrar/skaha/commit/7d6b3a979d0436acb4a9914d988f03e6a797b552))
* **tests:** fixed session tests to be more consistent and run ~60s ([19f0a6e](https://github.com/shinybrar/skaha/commit/19f0a6e00414bdd883ae699de1fb4edac5f5fba7))
* **tests:** fixed threading issue caused when one of the futures timesout ([ba55a38](https://github.com/shinybrar/skaha/commit/ba55a380ab5f8bd9c06e34a9c6cf543ea4ec7923))
* **tests:** fixes for session tests ([b3f3e48](https://github.com/shinybrar/skaha/commit/b3f3e4813953bc31e58c864f1f36f70a53bdac41))
* **typing:** multiple type hint fixes throughout the project ([a533481](https://github.com/shinybrar/skaha/commit/a53348166f8573af8c9780ded4a08f0fe95d6e44))


### Documentation

* **README:** updated with CI status ([175ffce](https://github.com/shinybrar/skaha/commit/175ffcecdeb6e89f45c078180b732f22890b6403))
* **skaha:** updated all docs ([04551c9](https://github.com/shinybrar/skaha/commit/04551c925320cc7bc068f554705975f2c429f4a5))

## [1.3.1](https://github.com/CHIMEFRB/skaha/compare/v1.3.0...v1.3.1) (2023-11-15)


### Bug Fixes

* **docs:** updated docs to include changelog, added reference for calling gpus in session.create ([e58f9be](https://github.com/CHIMEFRB/skaha/commit/e58f9be5ae07264bd8046d1980a742c4124d34a1))

## [1.3.0](https://github.com/CHIMEFRB/skaha/compare/v1.2.0...v1.3.0) (2023-11-14)


### Features

* **docs:** updates with a new ability to edit docs via PR ([aa2314d](https://github.com/CHIMEFRB/skaha/commit/aa2314d9f57778e7328f1c9f2fd64470a76af66b))


### Bug Fixes

* **docs:** updated readme ([4b81e7e](https://github.com/CHIMEFRB/skaha/commit/4b81e7ebfb0d86f50153edb07e9cf536a02ea802))

## [1.2.0](https://github.com/CHIMEFRB/skaha/compare/v1.1.1...v1.2.0) (2023-06-08)


### Features

* **client:** updated client to include skaha version in prep for v1 release ([e6360c0](https://github.com/CHIMEFRB/skaha/commit/e6360c07d9b305463e00f2f8293e6c9a2dc83f42))
* **overview:** added new overview module ([4a6336f](https://github.com/CHIMEFRB/skaha/commit/4a6336ff9d1ff3e05701848a500d35585cb0b154))


### Bug Fixes

* **deps:** updates ([5644e15](https://github.com/CHIMEFRB/skaha/commit/5644e15c5b28de2a54be2607d87ca2a3439e7659))
* **session:** fix for spawning sessions with gpus ([961f766](https://github.com/CHIMEFRB/skaha/commit/961f76673783f948a6cf0c3c2b70bb34e4d6d853))
* **tests:** fixed session tests, which now default spawn with name-{replica-id} format ([7e48031](https://github.com/CHIMEFRB/skaha/commit/7e48031281e5ed1e35b891655769977aa4d3fc44))

## [1.1.1](https://github.com/CHIMEFRB/skaha/compare/v1.1.0...v1.1.1) (2022-12-16)


### Documentation

* **readme:** update ([1b975b6](https://github.com/CHIMEFRB/skaha/commit/1b975b67da82a68d8c5072cc5739dcd024f39584))

## [1.1.0](https://github.com/CHIMEFRB/skaha/compare/v1.0.2...v1.1.0) (2022-12-16)


### Features

* **docs:** added build ([9049b92](https://github.com/CHIMEFRB/skaha/commit/9049b92b211bf4081b07f397a1c62ce058f3183b))
* **session:** create session now embeds two env variables into the container, REPLICA_COUNT and REPLICA_ID ([ecbf48a](https://github.com/CHIMEFRB/skaha/commit/ecbf48ad19536945f2359e75d0c3482a2e77feee))


### Bug Fixes

* **docs:** build command issue ([becbc60](https://github.com/CHIMEFRB/skaha/commit/becbc60fb605dd832a90b6b5e5941ce07dc092b6))
* **docs:** fixed build issue ([98b0543](https://github.com/CHIMEFRB/skaha/commit/98b0543f933087cac63955c40dd424285f70656f))

## [1.0.2](https://github.com/CHIMEFRB/skaha/compare/v1.0.1...v1.0.2) (2022-12-15)


### Bug Fixes

* **docs:** created documentation for the project ([e0f5483](https://github.com/CHIMEFRB/skaha/commit/e0f5483c2c72cd489258a84e3cb06d142a06f4da))


### Documentation

* **API-Reference:** changed where order of docs ([569d34f](https://github.com/CHIMEFRB/skaha/commit/569d34f00747fd1d2eff8f997ae277b63080df50))

## [1.0.1](https://github.com/CHIMEFRB/skaha/compare/v1.0.0...v1.0.1) (2022-12-15)


### Bug Fixes

* **env:** fixed multiple tests and added support for multiple env parameters ([c0500bf](https://github.com/CHIMEFRB/skaha/commit/c0500bf9c49a359f0b45205a5d1d6524144940f1))

## [1.0.0](https://github.com/CHIMEFRB/skaha/compare/v0.5.0...v1.0.0) (2022-12-14)


### ⚠ BREAKING CHANGES

* **session:** this is a signficant change, breaking all backwards compatibility
* **sessions:** skaha sessions api is no longer supported, the capability to manage multiple sessions is now provided by default with the skaha.session api itself

### Features

* **session:** added support for multiple session management ([219b74c](https://github.com/CHIMEFRB/skaha/commit/219b74cefc99264aca8f041a625dea30325c1f0d))
* **sessions:** skaha.sessions api deprecated ([e184663](https://github.com/CHIMEFRB/skaha/commit/e18466330e67a1b714da86062c79710fd459fa39))


### Bug Fixes

* **client:** updated session header to have the correct content-type ([3146e41](https://github.com/CHIMEFRB/skaha/commit/3146e418b6e075edcd5e34dd03e5b94879b17c08))
* **images:** images api now always prunes ([a436e21](https://github.com/CHIMEFRB/skaha/commit/a436e21085f00e5f6e5a408b1ff0bc486c6881f4))
* **pre-commit:** fixed broken pre-commit config ([baedb82](https://github.com/CHIMEFRB/skaha/commit/baedb825a63efca35573d064836b0928e2579029))
* **type-hints:** fixed broken hints ([9f4e9db](https://github.com/CHIMEFRB/skaha/commit/9f4e9dbba8a923d19e5e180f291c7ff216db9c64))
* **type-hints:** fixed broken type hints ([c1d1356](https://github.com/CHIMEFRB/skaha/commit/c1d1356bbba6642bb86e12b1aaf553094e83ea04))

## [0.5.0](https://github.com/CHIMEFRB/skaha/compare/v0.4.1...v0.5.0) (2022-12-14)


### Features

* **release-please:** implemented ([2ac9728](https://github.com/CHIMEFRB/skaha/commit/2ac972870d84876a74c7631f8af5cad453fab81e))


### Bug Fixes

* **gha:** fix to release action ([cc7b61a](https://github.com/CHIMEFRB/skaha/commit/cc7b61a472da50463f3159aac46f6aa3ae49e79c))
