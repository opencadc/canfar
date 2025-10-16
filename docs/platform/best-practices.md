# Best Practices for Astronomy Pipelines on CANFAR Science Platform

Developing astronomy data-processing pipelines for modern, cloud-native platforms (*like CANFAR Science Platform*) requires combining solid software practices with an understanding of scalable, containerized environments. Below are some of the key best practices, aimed at students and researchers building astronomy pipelines.

## Writing Scalable and Batch-Friendly Code

- **Design for Batch Execution**: Your pipeline code should run to completion without any manual intervention. This means no GUI pop-ups, no `input()` prompts, and no reliance on interactive environments. The science platform can execute your code in a batch session that has no interactive interface. Write your scripts to take parameters (like `filepaths` or `data_ids`) and then run autonomously, logging progress as needed.

- **Use Command-Line Arguments or Environment Variables**: Never hard-code dataset paths, filenames, or other configuration inside your code. Instead, pass them in so the pipeline is flexible. For example, use CLI tools like `argparse, click, or typer` to parse an `--input` file path and `--output` directory. Alternatively, read environment variables that the platform or user sets (e.g., your code might read an `$INPUT_DATA` env var).

    ```python
    import os, argparse

    if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", default=os.getenv("INPUT_FILE"))
        parser.add_argument("--output_dir", default=os.getenv("OUTPUT_DIR", "."))
        args = parser.parse_args()

        infile = args.input
        outfile = args.output_dir
        print(f"Processing {infile} and saving to {outfile}")
    ```

    ```
    python3 example.py --input something.fits --output_dir save/something/here
    ```

- **One Script for Interactive and Batch:** It’s helpful if the same code can run in JupyterLab (for debugging or exploration) and in batch mode (for large-scale runs). For example, if you develop your pipeline in a Jupyter notebook, you can export a Jupyter notebook to a Python script using, 
    
    ```bash
    jupyter nbconvert --to script notebook.ipynb
    ```

## Scaling Out vs. Scaling Up

- **Prefer Many Small Containers over One Big One**: Embrace horizontal scaling. The CANFAR Science Platform can easily run hundreds of container jobs in parallel, each on separate resources, but requesting a single container with 100× resources is impractical. For example, if you need to process 100 independent data files, it’s more efficient to run 100 containers with 1 CPU and 4 GB RAM each, than to run one container with 100 CPUs and 400 GB RAM doing it serially. The platform is optimized to handle large-scale parallel workloads for big datasets

    - *Why not one huge job?* Large containers (e.g. 32 cores, 128 GB RAM) are harder to schedule and could sit waiting in a queue. They also encourage monolithic processing that can’t be easily checkpointed. By contrast, many 1-core jobs can be scheduled as resources free up and can drastically reduce overall processing time by working concurrently.

    - *Memory is at a premium:* Splitting data into smaller chunks means each container uses less memory. This is crucial when dealing with terabyte-scale data – no single machine might have enough RAM to hold everything, but distributed processing can handle it piecewise. In practice: If each container processes, say, 50 GB of data at a time, a 100 TB dataset can be processed by 2000 such tasks in parallel.

- **Avoid Unnecessary Resource Requests:** Don’t request more CPU or RAM than your job actually needs. Start with a modest amount (the platform’s “flexible mode” will give resources as available) to prototype and test your pipeline. Only scale up to batch jobs after understanding the your resource requirements.

- **Utilize Parallel Libraries Cautiously:** Some Python libraries (NumPy, TensorFlow, etc.) will use multi-threading or multi-processing under the hood. Be mindful of this when running many containers to set these to the actual number of cores requested by your job. e.g. If you request 4 cores, set `OMP_NUM_THREADS=4` in your environment.

    ```python
    from canfar.sessions import Session

    session = Session()
    session_info = session.create(
        kind="headless",
        image="images.canfar.net/library/pipeline:latest",
        cores=4,
        ram=16,
        env={"OMP_NUM_THREADS": "4"}
    )
    ```

## Memory and I/O Efficiency

When dealing with large astronomy datasets, how you handle memory and I/O can make or break your pipeline and can be the difference between a job that finishes in minutes and one that takes hours.

- **Stream or Chunk Your Data:** Avoid loading extremely large datasets entirely into memory if possible. Libraries like `asttropy` can read FITS files in a memory-mapped mode (so data is loaded on-the-fly), and HDF5 (via `h5py`) allow chunked reads. If you have a 100 GB table, use `pandas` or `polars` to read it in chunks instead of `pd.read_csv` on the whole file at once. By processing data in streaming fashion, your job can handle inputs larger than RAM.

- **Free Memory Early:** In long-running containers that processes multiple files sequentially, make sure to free resources between files. Delete large arrays or data structures after use (e.g., `del big_array`) or wrap them in functions so they go out of scope. Python’s garbage collector will reclaim memory, but you can encourage it by not holding references longer than necessary. This is important when one container processes many tasks in sequence. If each file is 5 GB in memory and you process 10 of them in one container, you need to release each one before moving to the next to stay within a 5 GB budget.

## Saving Results

- **Write to Persistent Storage:** Remember that container file systems are ephemeral – once a session ends, anything written to the container’s own disk (other than mounted volumes) is lost. Always direct your outputs to the mounted storage provided by the platform e.g., your home directory, project space.

- **Unique and Descriptive Output Names:** When running many tasks in parallel, never have them all write to the same filename (like `output.fits` in the same folder). This would cause conflicts and overwrites. Instead, generate output filenames that incorporate a unique element, such as the input name or an index.

- **Organize Outputs Predictably:** Consider writing outputs of different pipeline stages to separate directories. For instance, raw data stays in `raw/`, calibration results in `calib/`, intermediate analysis in `analysis/`, and final catalogs or plots in `results/`. This structure helps both humans and programs (like a next-stage script) to locate what they need. It’s much easier to point a plotting script at a `results/` directory of processed files than to pick through one huge directory of mixed files.

- **Implement Checkpoints and Resume Logic:** If your pipeline can take hours or days to run, add checkpointing to save progress periodically. Break the pipeline into logical stages e.g., data reduction -> feature extraction -> modeling -> results. After each stage, output data to disk (or a database). If a later stage needs to be re-run, you don’t have to redo earlier stages.


## Headless Processing vs. GUI Tools

- **Avoid GUI Tools in Batch Pipelines:** Many traditional astronomy tools (like DS9, TOPCAT, IRAF GUI, etc.) require X11 or a graphical interface. These are not suited for automated pipelines running on a cluster. In a containerized platform, there may not be an easy display available for GUI apps, and attempts to use virtual displays or X forwarding can be fragile. It’s best to use command-line or library equivalents for any analysis.

- **Separate Interactive Analysis from Batch Jobs:** If you do need to use a GUI-based tool for some part of your work (for instance, visually inspecting a subset of data or interactive data exploration), do that in a dedicated interactive session separate from the batch pipeline. The platform provides specialized sessions for this purpose.

## Managing Dependencies and Python Environments

- **Using Modern Dependency Managers:** The platform’s base images come with tools like uv, pipx, and conda pre-installed *(Soon, Work in Progress)*. Prefer these for managing Python packages:
    - **uv:** a fast Python package manager that can replace pip/venv workflows. It allows you to declare dependencies inside your scripts and automatically handles virtual environments for each run
    - **pipx:** for installing and running standalone CLI tools in isolated environments, ensuring they don’t pollute your main env.
    - **conda/mamba:** for packages that are easier to get from conda (especially if C/C++ libs are needed). Base containers *(Soon, Work in Progress)* include conda (via mamba for speed).


- **Inline Dependency Declaration with uv:** One powerful pattern is to declare your script’s requirements using `PEP 723 style` metadata. For example, using `uv`, you can add a header to your Python script listing its packages. When you run this script with uv run, uv will create an isolated environment with these packages installed, so your script runs with exactly the needed libraries. This approach ensures anyone running the script (or any container executing it) gets the correct dependencies without manual setup.

    ```python
    # /// script.py
    # dependencies = [
    #   "astropy",
    #   "photutils>=1.9",
    #   "polars"
    # ]
    # ///
    import astropy
    import photutils
    import polars
    ```

    ```bash
    uv run python script.py
    ```

- **Keep Environments Reproducible:** Avoid “it works on my machine | session” issues by documenting dependencies. If you installed something interactively in Jupyter, add it to your with your manager of choice.


## Container Packaging

- **Group tools by logical pipeline step:** - Don't create a monolithic container with all tools for every stage or split every tool into its own micro-container. Create one container per logical pipeline step, bundling all tools needed for that step—whether they're interactive or batch-oriented.

- **Reuse** the same container for both interactive testing (e.g. JupyterLab) and headless batch execution of the same code. This ensures consistency, debuggability, and minimizes surprises in batch jobs.

- **Test Locally:** Before scaling up, test your container build and functionality on a small dataset locally or in an interactive session. This ensures the environment has everything needed.

#### Keep Containers Lean 

- **Use Official Base Images (Soon, Work in Progress):** If building your own container image for a pipeline, start with a provided base image rather than starting from scratch. For example, the `base:22.04` image is a good general starting point – and it comes with `uv, pipx, conda` pre-installed and configured.
    ```dockerfile
    FROM images.canfar.net/library/base:22.04
    ```

- **Keep Images Lightweight:** Minimize what you add to the container. Uninstall unnecessary packages and avoid including large test data or docs inside the image. A smaller image pulls faster and uses less storage, benefiting batch runs. Use a .dockerignore file to exclude files like docs, tests, and git directories from the build context

- **Optimize Dockerfile Layers:** Combine related commands into single `RUN` statements and clean up after installations to reduce image size. For example, update and install Linux packages in one layer, then remove package lists and caches:

```dockerfile
# Combining update, install, and cleanup in one layer
RUN apt-get update && apt-get install -y \
    astrometry.net sextractor \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
```