# Contributing to CANFAR

Thank you for considering contributing to the canfar project! We welcome contributions from everyone. Please follow the guidelines below to help us maintain a high-quality codebase.

We follow the [Contributor Convenant of Code of Conduct](https://github.com/opencadc/canfar/blob/main/CODE_OF_CONDUCT.md). If you wish to contribute to canfar, please make sure to familiarize yourself with it.

Contributions are not limited to just code. You can help us by:

- Answering questions on the [Discussions board](https://github.com/opencadc/canfar/discussions)
- Improving the [Documentation](https://github.com/opencadc/canfar/tree/main/docs)
- Reporting bugs and suggesting features via [GitHub Issues](https://github.com/opencadc/canfar/issues) (see our [Bug Reporting Guide](https://opencadc.github.io/canfar/bug-reports/) for detailed instructions)
- Spreading the word about CANFAR

## How to Contribute Code

### 1. Fork the Repository

Start by forking the repository on GitHub. This will create a copy of the project under your GitHub account.

### 2. Clone Your Fork

Clone your forked repository to your local machine:

```bash
git clone https://github.com/your-username/canfar.git
cd canfar
```

### 3. Set Up Your Development Environment

- CANFAR uses *uv* for for package, project and dependency management. To install *uv*, please refer to the [astral-uv documentation](https://docs.astral.sh/uv/getting-started/installation/).
- You need a valid CANFAR account and access to the CANFAR Science Platform. To request access, [please request an account with the Canadian Astronomy Data Centre (CADC)](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html).

To setup the development environment, simply run:

```bash
uv python install 3.13
uv venv --python 3.13
uv sync --all-extras --dev
```

These commands will install the Python version, create a virtual environment, and install all dependencies required for development.

!!! note "Alternative Tooling"
    While this project uses *uv* for dependency and virtual environment management, you are welcome to use other tools like *pip*, *conda*, or *virtualenv*. The `pyproject.toml` file contains all the necessary information for these tools to create a compatible environment.

Skaha uses *pre-commit* to manage the development workflow. To install the pre-commit hooks, simply run:

```bash
uv run pre-commit install --hook-type commit-msg
```

### Contributing to Documentation

To contribute to the documentation, you first need to set up the project as described in the "Set Up Your Development Environment" section. The command `uv sync --all-extras --dev` will install all necessary dependencies, including the ones for building the documentation.

Once the dependencies are installed, you can build and serve the documentation locally by running:

```bash
uv run mkdocs build
uv run mkdocs serve
```

This will start a local server, and you can view the documentation in your web browser at the address indicated in the output (usually `http://127.0.0.1:8000`). The documentation will automatically reload when you make changes to the files.

### 4. Make Your Changes

Make your changes. Please make sure to add tests for your changes if applicable.

### 5. Run the Tests

To run tests for Skaha, you need to have a valid CANFAR account and access to the CANFAR Science Platform. To generate a certificate, please refer to the [get started](client/get-started.md) section.

```bash
uv run pytest
```

#### Running Tests Efficiently

Some tests in the Skaha test suite are marked as "slow" because they involve network operations, waiting for session states, or other time-consuming operations. These tests can take several minutes to complete.

**Run all tests (including slow ones):**
```bash
uv run pytest
```

**Skip slow tests for faster development:**
```bash
uv run pytest -m "not slow"
```

**Run only slow tests:**
```bash
uv run pytest -m "slow"
```

The slow tests are primarily integration tests that interact with the CANFAR Science Platform and include:
- Session creation and management tests
- Log retrieval tests
- Authentication timeout tests
- Session statistics tests

For rapid development and testing, it's recommended to use `-m "not slow"` to skip these time-consuming tests during your development cycle, and run the full test suite before submitting your pull request.

### 6. Commit Your Changes

Skaha uses the [conventional commit messages](https://www.conventionalcommits.org/en/v1.0.0/) standard to ensure the commit history human and machine readable. Skaha ships with a tool called `commitizen` that helps you craft commit messages in the correct format.

```bash
git add files/you/changed.py
uv run cz commit
```

At this point, you will also see *pre-commit* hooks running to check your code for any issues and ensure that the code is linted and formatted correctly.

### 7. Push Changes to Your Fork

Push your changes to your forked repository:

```bash
git push
```

### 8. Create a Pull Request

Once your changes are pushed to your fork, you can create a pull request from your forked repository to the main Skaha repository. The maintainers will review your changes and merge them if everything is in order.

### 9. Celebrate

Congratulations! You've made it through the contribution process! Now it's time to celebrate your hard work. Here are a few fun ways to do so:

- **Dance Party**: Put on your favorite tunes and have a solo dance party in your living room. Bonus points for using a disco ball!
- **Snack Attack**: Treat yourself to your favorite snack. Whether it's pizza, ice cream, or a healthy smoothie, you deserve it!
- **Virtual High-Five**: Send a virtual high-five to your fellow contributors. You can even use a GIF for extra flair!
- **Meme It Up**: Create a meme about your contribution journey. Share it in the Discussions board for a good laugh!
- **Celebrate with Code**: Write a fun piece of code that does absolutely nothing but prints "I did it!" to the console. Because why not?

Remember, every contribution counts, and you’ve just made the Skaha project a little better. Now go forth and celebrate like the coding rockstar you are!
