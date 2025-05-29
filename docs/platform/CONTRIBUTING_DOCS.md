# Contributing to the CANFAR Science Platform Documentation

Thank you for your interest in contributing to the CANFAR Science Platform documentation! Your help is invaluable in keeping our documentation accurate, up-to-date, and comprehensive for all users.

## Documentation Philosophy

Our goal is to provide clear, concise, and practical documentation that caters to both new and advanced users. We aim for:

- Accuracy: Information should be technically correct and reflect the current state of the platform.
- Clarity: Explanations should be easy to understand, avoiding unnecessary jargon.
- Completeness: Covering all essential aspects of the platform and its usage.
- User-Friendliness: Well-structured, navigable, and accessible.

## Getting Started

### Local Development Setup

To preview your changes locally before submitting them, you'll need to set up MkDocs:

1. **Prerequisites:**

    - Python 3.x
    - pip (Python package installer)

2. **Clone the Repository:**

    ```bash
    git clone https://github.com/opencadc/science-containers.git
    cd science-containers
    ```

3. **Install Dependencies:**
    We use `poetry` for dependency management. If you don't have it, install it first (see [Poetry's official documentation](https://python-poetry.org/docs/#installation)).

    ```bash
    poetry install
    ```

    This will create a virtual environment and install all necessary packages, including MkDocs and the Material theme, as defined in `pyproject.toml` and `poetry.lock`.

4. **Run the Development Server:**
    Activate the virtual environment created by Poetry and start the MkDocs live-reloading server:

    ```bash
    poetry shell
    mkdocs serve
    ```

    Open your browser and navigate to `http://127.0.0.1:8000` to see the documentation. Changes you make to the documentation files will automatically reload the site in your browser.

### Documentation Structure

The documentation is organized into several main sections, as defined in the `nav` section of the `mkdocs.yml` file. Familiarize yourself with this structure to understand where your contributions might fit best.

- `docs/` : Contains all Markdown files for the documentation.
  - `user-guide/`: For general users, covering basic operations and usage.
  - `tutorials/`: Step-by-step guides for specific workflows.
  - `developer-guide/`: For developers and advanced users, covering container building, API usage, etc.
  - `reference-material/`: Technical specifications, lists, and other reference content.
  - `help/`: FAQs and support information.

## Making Changes

1. **Find or Create a Page:**

    - To modify an existing page, navigate to the relevant Markdown file in the `docs/` directory.
    - To add a new page, create a new `.md` file in the appropriate subdirectory. You will also need to add it to the `nav` section in `mkdocs.yml`.

2. **Edit Content:**

    - Use Markdown syntax for formatting.
    - Follow our [Markdown Style Guide](#markdown-style-guide).

3. **Use the "Edit this page" Link:**
    Most pages have an "Edit this page" link (pencil icon) in the top right corner. This link, configured via `edit_uri` in `mkdocs.yml`, will take you directly to the corresponding file on GitHub, where you can suggest changes through a pull request. This is great for small fixes. For larger contributions, the local development setup is recommended.

4. **Commit and Push:**
    Commit your changes with a clear and descriptive commit message.

    ```bash
    git add .
    git commit -m "docs: Describe your change clearly"
    git push origin your-branch-name
    ```

5. **Submit a Pull Request:**
    Go to the [opencadc/science-containers GitHub repository](https://github.com/opencadc/science-containers/) and open a pull request from your branch to the `main` branch. Provide a clear description of your changes in the pull request.

## Markdown Style Guide

- **Headings:** Use `#` for H1 (page title, usually one per page), `##` for H2, `###` for H3, etc.
- **Code Blocks:** Use triple backticks ` ``` ` for code blocks. Specify the language for syntax highlighting (e.g., ` ```python ` or ` ```bash `).

    ```bash
    # Example of a bash command
    echo "Hello, CANFAR!"
    ```

- **Inline Code:** Use single backticks for inline code, like `variable_name` or `command --option`.
- **Admonitions:** Use admonitions to highlight important information. MkDocs Material supports various types:

    ```markdown
    !!! note
        This is a note.

    !!! tip "Pro Tip"
        This is a helpful tip.

    !!! warning
        This is a warning.

    !!! danger "Critical"
        This is a critical warning.

    !!! abstract "Summary"
        This is an abstract or summary.

    !!! example
        This is an example.
    ```

- **Links:** Use standard Markdown links: `[Link text](URL)`. For internal links, use relative paths to other `.md` files (e.g., `[Link to another page](../user-guide/some-page.md)`).
- **Images:** Store images in an `images` subdirectory within the relevant section (e.g., `docs/user-guide/images/`). Link them using `![Alt text](images/my-image.png)`.
- **Lists:** Use hyphens (`-`) or asterisks (`*`) for unordered lists, and numbers (`1.`) for ordered lists.

## Writing for Different Audiences

- **New Users:**
  - Avoid jargon where possible, or explain it clearly.
  - Provide step-by-step instructions.
  - Focus on common tasks and getting started.
- **Advanced Users:**
  - Provide technical details and options.
  - Include information on automation, APIs, and advanced configurations.
  - Assume a base level of familiarity with relevant technologies.

## Questions?

If you have questions about contributing, feel free to open an issue on the GitHub repository or reach out to the CANFAR team.

Thank you for helping us improve the CANFAR Science Platform documentation!
