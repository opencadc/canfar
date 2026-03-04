# Software Repositories (CVMFS)

**Accessing thousands of scientific software packages through global read-only repositories.**

!!! abstract "🎯 What is CVMFS?"
    The **CernVM File System (CVMFS)** is a distributed, read-only filesystem designed to deliver software to large-scale computing environments. On CANFAR, all sessions (Notebooks, Desktops, and Batch) have access to CVMFS, providing instant access to software stacks maintained by the **Digital Research Alliance of Canada (Alliance)**.
    
    CVMFS is **not** a general-purpose writable project storage system: it is optimized for publishing and distributing versioned, mostly immutable software/reference trees (read-many, write-by-maintainers), while your active notebooks, code, intermediate results, and team-shared working files should live in writable storage (for example, `/arc` on CANFAR).

## 🚀 Why Use CVMFS?

Traditional software management often involves complex installations, dependency conflicts, and large container images. CVMFS changes this by providing:

*   **Instant Access**: Thousands of pre-built packages are available without any installation.
*   **Consistency**: The same software environment used on Alliance clusters (like Fir or Nibi) is available directly in your CANFAR session.
*   **Resource Efficiency**: Software is downloaded on-demand and cached, keeping container images small and fast to launch.

## ✅ Pros and ⚠️ Trade-offs (User Perspective)

From a user perspective, CVMFS is often the fastest way to access large shared scientific software stacks because repositories are mounted read-only, fetched on demand, and cached locally.

**Pros**

*   **Fast access to large software stacks**: You can use pre-installed tools without rebuilding a large container or reinstalling packages in every session.
*   **On-demand, cached delivery**: CVMFS fetches only the files you actually touch, then reuses them from cache, which is efficient for interactive work.
*   **Consistent shared environments**: The same published software stack can be exposed across many systems, which helps reproducibility and collaboration.
*   **Curated by maintainers**: Shared stacks are typically built and maintained by dedicated teams, which reduces user setup burden for common tools.
*   **Works well with containers**: A small container can provide the runtime base while CVMFS provides the heavy software stack.

**Trade-offs**

*   **Read-only applies to `/cvmfs`, not your workspace**: You cannot install into `/cvmfs`, but you can still install in your home/project space (on CANFAR, under mounted `/arc`) or build software into your own container.
*   **First use can be slower**: Initial access may take longer while metadata/files are fetched and cached; repeated use is usually faster.
*   **What is available depends on maintainers**: If a package/version is not published in the shared repository, you may need a local environment or custom container.
*   **Site-specific tooling may vary**: On CANFAR/Alliance, using CVMFS software often involves environment modules (`module load`); other CVMFS deployments may use different setup methods.
*   **Custom environments are still important**: For writable installs, rapid iteration, or tightly pinned dependencies, use a virtualenv/conda env in your workspace and/or a custom container on top of the shared stack.

!!! warning "Common Gotcha: Browsing `/cvmfs`"
    A common surprise is that running `ls /cvmfs` may appear empty. This is because repositories are mounted *lazily* only when you access a known path. You cannot simply browse `/cvmfs` like a normal directory to discover software.
    
    **Practical remedies:**
    
    *   **Use documented repository paths**: On CANFAR, always start with `/cvmfs/soft.computecanada.ca/`.
    *   **Provide shortcuts in docs/examples**: Include copy/paste-ready `source` and `module` commands in your own team's documentation to avoid guesswork.

## 🧠 Advanced: CVMFS + Containers (Hybrid Model)

In modern platforms, CVMFS usually complements containers rather than replacing them: a small container image provides the base OS/runtime, CVMFS provides large shared software trees on demand, and your home/project storage remains the writable layer for notebooks, code, and custom packages. This hybrid approach improves startup time and reduces image size while preserving flexibility for user-specific environments.

On CANFAR, CVMFS caching happens on the Kubernetes worker node and is shared by sessions running on that node. This means one user's first access to a tool may warm the cache for later sessions scheduled on the same node, while a newly scaled or different node may behave like a cold cache.

### Platform Evolution
Where this can go next:

*   **Richer shared environments**: Publish more curated stacks (for example, domain-specific Python/Conda environments) for common workflows.
*   **Team-maintained software repositories**: Small groups can publish and version their own CVMFS software trees (with appropriate operational support), reducing reliance on one central software stack.
*   **Container + CVMFS hybrid workflows**: Keep containers small and stable, and move large, frequently reused software into CVMFS for faster startup and less image churn.
*   **Improved cache/proxy topology**: Node-local caches plus local HTTP proxy caches can significantly reduce repeated downloads and external bandwidth usage at scale.
*   **Collaborative reproducibility**: Treat CVMFS-published stacks as versioned, documented shared environments, while keeping writable collaboration artifacts (code, notebooks, data products) in `/arc` or other project storage.

### Pointers for Advanced Readers

*   **[CVMFS Official Documentation](https://cvmfs.readthedocs.io/en/stable/)**: architecture, client/cache behaviour, and operations guidance.
*   **[Kubernetes CVMFS CSI driver](https://github.com/cvmfs-contrib/cvmfs-csi)**: mounting CVMFS repositories into pods in cloud-native environments.
*   **[EESSI (European Environment for Scientific Software Installations)](https://www.eessi.io/)**: an example of a large cross-site scientific software stack distributed via CVMFS.
## 🛠️ Accessing the Software

The Alliance software stack is mounted at `/cvmfs/soft.computecanada.ca/`. Accessing it is a two-step process:

1.  **Initialize the environment**: Source the profile to enable `module` commands.
2.  **Load your software**: Use `module load` to add specific packages to your path.

### Example: Before vs. After CVMFS

Suppose you need a specific Python version or a package not included in the standard `astroml` container.

=== "Step 0: Before CVMFS"
    Notice that the environment is limited to what is pre-installed in your container.
    ```bash
    # Current python version might be 3.12
    python --version
    # Output: Python 3.12.x
    ```

=== "Step 1: Enable CVMFS"
    Source the Alliance bash profile to enable the environment module system.
    ```bash
    source /cvmfs/soft.computecanada.ca/config/profile/bash.sh
    ```

=== "Step 2: Find & Load Software"
    Search for the software you need and load it.
    ```bash
    # See available python versions
    module avail python

    # Load Python 3.10
    module load python/3.10
    ```

=== "Step 3: Verification"
    Verify that your environment has changed.
    ```bash
    python --version
    # Output: Python 3.10.x
    ```

## 🔗 Learning More

The Alliance provides extensive documentation on their software environment. Since CANFAR mounts the same CVMFS repositories, these guides apply directly to your sessions:

*   **[Accessing CVMFS](https://docs.alliancecan.ca/wiki/Accessing_CVMFS)**: Technical overview of the filesystem.
*   **[Using Modules](https://docs.alliancecan.ca/wiki/Using_modules)**: Detailed guide on the `module` command (avail, load, list, purge).
*   **[Available Software](https://docs.alliancecan.ca/wiki/Available_software)**: Searchable list of the thousands of packages available via CVMFS.

!!! tip "Persistence"
    Environment changes made via `module load` are session-specific. If you want specific modules to be loaded every time you open a terminal, you can add the `source` and `module load` commands to your `~/.bashrc` file (located in `/arc/home/[user]/.bashrc`).
