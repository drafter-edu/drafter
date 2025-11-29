.. _local_setup:

======================================
Local Python Development Setup Guide
======================================

This guide will walk you through setting up your computer for Python development using Visual Studio Code (VS Code).
By the end of this guide, you will have a fully functional development environment with Git, Python, VS Code, and all the tools you need to write, test, and share your code.

.. note::
    These instructions are written for beginners. Each step explains not just *what* to do, but *why* you're doing it.
    Follow the steps in order, as each step builds on the previous ones.

.. contents:: Table of Contents
   :local:
   :depth: 2

Step 1: Install Git
===================

**What is Git?**
Git is a version control system that tracks changes to your code over time. It lets you save snapshots of your work, go back to previous versions if something breaks, and collaborate with others. Almost all professional developers use Git.

**Why do you need Git?**
You'll use Git to download code from GitHub (a website that hosts code), save your own code changes, and submit your work.

.. tabs::

   .. tab:: Windows

      1. Go to the Git download page: https://git-scm.com/downloads/win

      2. Click the **"Click here to download"** link to download the installer (it will download a file like ``Git-2.xx.x-64-bit.exe``)

         .. note::
            [SCREENSHOT NEEDED: Git download page for Windows showing the download link]

      3. Run the downloaded installer by double-clicking on it

      4. **Important:** During installation, you will see many screens with options. For most screens, you can just click **Next** to accept the default settings. However, pay attention to these settings:

         - On the "Adjusting your PATH environment" screen, make sure **"Git from the command line and also from 3rd-party software"** is selected (this is usually the default)
         - On the "Configuring the line ending conversions" screen, keep the default setting

         .. note::
            [SCREENSHOT NEEDED: Git installer PATH environment screen showing the recommended option]

      5. Click **Install** and wait for the installation to complete

      6. Click **Finish** when done

      **Verify the installation:**

      1. Press ``Windows key + R`` to open the Run dialog
      2. Type ``cmd`` and press Enter to open Command Prompt
      3. Type ``git --version`` and press Enter
      4. You should see something like ``git version 2.xx.x`` - this means Git is installed correctly!

         .. note::
            [SCREENSHOT NEEDED: Command Prompt showing successful git --version output]

   .. tab:: Mac

      There are two ways to install Git on Mac. Choose the one that works best for you:

      **Option A: Install via Xcode Command Line Tools (Simplest)**

      1. Open the **Terminal** application:
         
         - Press ``Command + Space`` to open Spotlight Search
         - Type ``Terminal`` and press Enter

      2. In Terminal, type the following command and press Enter:

         .. code-block:: bash

            xcode-select --install

      3. A popup will appear asking you to install the command line developer tools. Click **Install**

         .. note::
            [SCREENSHOT NEEDED: Xcode Command Line Tools installation popup]

      4. Wait for the installation to complete (this may take several minutes)

      **Option B: Install via Homebrew (Alternative)**

      If you already have Homebrew installed, you can install Git with:

      .. code-block:: bash

         brew install git

      **Verify the installation:**

      1. Open Terminal (if not already open)
      2. Type ``git --version`` and press Enter
      3. You should see something like ``git version 2.xx.x`` - this means Git is installed correctly!

         .. note::
            [SCREENSHOT NEEDED: Terminal showing successful git --version output on Mac]


Step 2: Install Python
======================

**What is Python?**
Python is a programming language - it's the language you'll use to write your code. The Python interpreter reads your code and runs it.

**Why do you need Python?**
You need Python installed on your computer to run Python programs. While VS Code is where you'll write your code, Python is what actually executes it.

.. tabs::

   .. tab:: Windows

      1. Go to the Python download page: https://www.python.org/downloads/

      2. Click the large yellow **"Download Python 3.x.x"** button to download the installer

         .. note::
            [SCREENSHOT NEEDED: Python download page showing the download button]

      3. Run the downloaded installer by double-clicking on it

      4. **IMPORTANT:** On the first screen of the installer, make sure to check the box that says **"Add Python to PATH"** at the bottom of the window. This is crucial!

         .. note::
            [SCREENSHOT NEEDED: Python installer first screen with "Add Python to PATH" checkbox highlighted]

      5. Click **"Install Now"**

      6. Wait for the installation to complete, then click **Close**

      **Verify the installation:**

      1. Open a **new** Command Prompt window (close any existing ones first):
         - Press ``Windows key + R``
         - Type ``cmd`` and press Enter

      2. Type ``python --version`` and press Enter

      3. You should see something like ``Python 3.x.x`` - this means Python is installed correctly!

         .. note::
            [SCREENSHOT NEEDED: Command Prompt showing successful python --version output]

   .. tab:: Mac

      1. Go to the Python download page: https://www.python.org/downloads/

      2. Click the large yellow **"Download Python 3.x.x"** button

         .. note::
            [SCREENSHOT NEEDED: Python download page for Mac]

      3. Open the downloaded ``.pkg`` file and follow the installation instructions

      4. Click **Continue** through the screens, then **Install**

      5. Enter your Mac password when prompted, and wait for installation to complete

      **Verify the installation:**

      1. Open Terminal (``Command + Space``, type ``Terminal``, press Enter)

      2. Type ``python3 --version`` and press Enter

      3. You should see something like ``Python 3.x.x`` - this means Python is installed correctly!

         .. note::
            [SCREENSHOT NEEDED: Terminal showing successful python3 --version output on Mac]

      .. warning::
         On Mac, you should use ``python3`` instead of ``python`` to run Python 3. The ``python`` command on Mac often refers to an older version of Python.


Step 3: Install Visual Studio Code (VS Code)
=============================================

**What is VS Code?**
Visual Studio Code (VS Code) is a code editor - it's like a word processor, but designed specifically for writing code. It has features like syntax highlighting (coloring your code to make it easier to read), error detection, and extensions that add extra functionality.

**Why do you need VS Code?**
While you could write Python code in any text editor (even Notepad), VS Code makes coding much easier with features like auto-completion, error highlighting, and integrated terminal access.

.. tabs::

   .. tab:: Windows

      1. Go to the VS Code download page: https://code.visualstudio.com/Download

      2. Click the **Windows** download button (it will download a file like ``VSCodeUserSetup-x64-1.xx.x.exe``)

         .. note::
            [SCREENSHOT NEEDED: VS Code download page showing the Windows download button]

      3. Run the downloaded installer

      4. Accept the license agreement and click **Next**

      5. On the "Select Additional Tasks" screen, we recommend checking these boxes:
         
         - **"Add 'Open with Code' action to Windows Explorer file context menu"** - lets you right-click on files to open them in VS Code
         - **"Add 'Open with Code' action to Windows Explorer directory context menu"** - lets you right-click on folders to open them in VS Code
         - **"Add to PATH"** - lets you open VS Code from the command line

         .. note::
            [SCREENSHOT NEEDED: VS Code installer showing the additional tasks checkboxes]

      6. Click **Next**, then **Install**

      7. When installation completes, you can check **"Launch Visual Studio Code"** and click **Finish**

   .. tab:: Mac

      1. Go to the VS Code download page: https://code.visualstudio.com/Download

      2. Click the **Mac** download button (it will download a ``.zip`` file)

         .. note::
            [SCREENSHOT NEEDED: VS Code download page showing the Mac download button]

      3. Open the downloaded ``.zip`` file (usually in your Downloads folder). This will extract the VS Code application

      4. Drag the **Visual Studio Code.app** to your **Applications** folder

         .. note::
            [SCREENSHOT NEEDED: Dragging VS Code to Applications folder on Mac]

      5. Open VS Code by going to your Applications folder and double-clicking on **Visual Studio Code**

      6. If you see a warning that says "Visual Studio Code is an app downloaded from the Internet. Are you sure you want to open it?", click **Open**

      **Adding VS Code to your PATH (recommended):**

      This lets you open VS Code from the Terminal by typing ``code``.

      1. Open VS Code
      2. Press ``Command + Shift + P`` to open the Command Palette
      3. Type ``shell command`` and select **"Shell Command: Install 'code' command in PATH"**
      4. Click **OK** on any dialogs that appear

         .. note::
            [SCREENSHOT NEEDED: VS Code Command Palette showing "Install code command in PATH"]


Step 4: Install the Python Extension for VS Code
================================================

**What is the Python Extension?**
The Python extension adds Python-specific features to VS Code, like intelligent code completion, debugging, and the ability to run Python code directly from the editor.

**Why do you need it?**
Without this extension, VS Code is just a text editor. With the extension, VS Code understands Python and can help you write better code faster.

1. Open VS Code

2. Click on the **Extensions** icon in the left sidebar (it looks like four squares, with one square separated from the others)

   .. note::
      [SCREENSHOT NEEDED: VS Code sidebar showing the Extensions icon highlighted]

3. In the search box at the top, type ``Python``

4. Find the extension called **"Python"** by Microsoft (it should be the first result with millions of downloads)

   .. note::
      [SCREENSHOT NEEDED: VS Code Extensions marketplace showing the Python extension by Microsoft]

5. Click the **Install** button

6. Wait for the installation to complete. You should see the button change to "Installed" or show a gear icon

**Verify the installation:**

1. Press ``Ctrl + Shift + P`` (Windows) or ``Command + Shift + P`` (Mac) to open the Command Palette
2. Type ``Python: Select Interpreter`` and press Enter
3. You should see your installed Python version in the list. Select it.

   .. note::
      [SCREENSHOT NEEDED: VS Code Python interpreter selection showing the installed Python version]


Step 5: Install UV
==================

**What is UV?**
UV is a fast Python package manager. It helps you install Python libraries (pre-written code that you can use in your projects) and manage project dependencies (libraries that your project needs to work).

**Why do you need UV?**
When you download a Python project, it often requires additional libraries to run. UV makes it easy to install all these libraries with a single command. It's much faster than the traditional ``pip`` tool.

.. tabs::

   .. tab:: Windows

      1. Open **PowerShell** (not Command Prompt):
         
         - Press ``Windows key``
         - Type ``PowerShell``
         - Click on **Windows PowerShell** (make sure it's PowerShell, not Command Prompt)

         .. note::
            [SCREENSHOT NEEDED: Windows search showing PowerShell]

      2. Copy and paste this command into PowerShell, then press Enter:

         .. code-block:: powershell

            powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

      3. Wait for the installation to complete

      4. **Close PowerShell and open a new one** for the changes to take effect

      **Verify the installation:**

      1. In the new PowerShell window, type ``uv --version`` and press Enter

      2. You should see a version number like ``uv 0.x.x`` - this means UV is installed correctly!

         .. note::
            [SCREENSHOT NEEDED: PowerShell showing successful uv --version output]

   .. tab:: Mac

      1. Open **Terminal** (``Command + Space``, type ``Terminal``, press Enter)

      2. Copy and paste this command, then press Enter:

         .. code-block:: bash

            curl -LsSf https://astral.sh/uv/install.sh | sh

      3. Wait for the installation to complete

      4. **Close Terminal and open a new one** for the changes to take effect

      **Verify the installation:**

      1. In the new Terminal window, type ``uv --version`` and press Enter

      2. You should see a version number like ``uv 0.x.x`` - this means UV is installed correctly!

         .. note::
            [SCREENSHOT NEEDED: Terminal showing successful uv --version output on Mac]


Step 6: Setup GitHub Copilot
============================

**What is GitHub Copilot?**
GitHub Copilot is an AI-powered coding assistant that suggests code as you type. It can help you write code faster by suggesting completions, entire functions, and even helping you understand unfamiliar code.

**Why should you use it?**
As a student, you have free access to GitHub Copilot. It's like having a helpful coding partner that can suggest solutions and help you learn new programming patterns.

**Prerequisites:**

- You need a GitHub account. If you don't have one, go to https://github.com/signup and create a free account.
- You should apply for the GitHub Student Developer Pack (see the last section of this guide) to get free access to Copilot.

**Installing the GitHub Copilot Extension:**

1. Open VS Code

2. Click on the **Extensions** icon in the left sidebar

3. In the search box, type ``GitHub Copilot``

4. Find and install **"GitHub Copilot"** by GitHub (look for the official one with millions of downloads)

   .. note::
      [SCREENSHOT NEEDED: VS Code Extensions showing GitHub Copilot extension]

5. Click **Install**

6. After installation, you'll see a prompt to sign in to GitHub. Click **Sign in to GitHub**

   .. note::
      [SCREENSHOT NEEDED: VS Code showing the GitHub sign-in prompt for Copilot]

7. Your browser will open. Log in to your GitHub account if prompted, and authorize VS Code to access your account

8. Return to VS Code. You should see that Copilot is now active.

**How to use Copilot:**

Once Copilot is activated, it will automatically suggest code as you type. When you see a gray suggestion appear:

- Press ``Tab`` to accept the suggestion
- Press ``Esc`` to dismiss it
- Keep typing to ignore it and write your own code

You can also:

- Press ``Ctrl + Enter`` (Windows) or ``Command + Enter`` (Mac) to see multiple suggestions
- Type a comment describing what you want, and Copilot will suggest code to match

.. note::
   Copilot suggestions are helpful, but always review them before accepting. The suggestions are not always correct, and understanding what the code does is important for your learning.


Step 7: Fork and Clone a Repository
===================================

**What is Forking?**
Forking creates your own copy of someone else's project on GitHub. This copy belongs to you, so you can make changes without affecting the original project.

**What is Cloning?**
Cloning downloads a copy of a GitHub repository to your computer so you can work on it locally.

**Why do you need to do this?**
When working on assignments or collaborative projects, you'll often start with code that someone else has written. Forking gives you your own copy to work on, and cloning puts that copy on your computer.

**Step 7a: Fork the Repository**

1. Go to the repository link provided by your instructor (this will be a GitHub URL like ``https://github.com/username/repository-name``)

2. Make sure you are logged into your GitHub account

3. Click the **Fork** button in the top-right corner of the page

   .. note::
      [SCREENSHOT NEEDED: GitHub repository page showing the Fork button]

4. On the "Create a new fork" page, keep the default settings and click **Create fork**

5. Wait for GitHub to create your fork. You'll be taken to your forked repository (notice the URL now shows your username)

   .. note::
      [SCREENSHOT NEEDED: Forked repository showing the user's username in the URL]

**Step 7b: Clone the Repository to Your Computer**

1. On your forked repository page, click the green **Code** button

2. Make sure **HTTPS** is selected (not SSH), and click the copy icon to copy the URL

   .. note::
      [SCREENSHOT NEEDED: GitHub Code button dropdown showing the HTTPS URL and copy button]

3. Open VS Code

4. Press ``Ctrl + Shift + P`` (Windows) or ``Command + Shift + P`` (Mac) to open the Command Palette

5. Type ``Git: Clone`` and select it

   .. note::
      [SCREENSHOT NEEDED: VS Code Command Palette showing Git: Clone option]

6. Paste the URL you copied and press Enter

7. Choose a folder on your computer where you want to save the project (for example, a "Projects" folder in your Documents)

8. Click **Select as Repository Destination**

9. VS Code will download the repository. When it asks "Would you like to open the cloned repository?", click **Open**

   .. note::
      [SCREENSHOT NEEDED: VS Code dialog asking to open the cloned repository]

You now have the project on your computer and open in VS Code!


Step 8: Install Dependencies and Run Tests
===========================================

**What are Dependencies?**
Dependencies are external libraries that a project needs to work. Most Python projects use libraries written by other developers to avoid reinventing the wheel.

**What are Tests?**
Tests are code that checks if other code works correctly. Running tests tells you if the project is set up correctly and if your changes break anything.

**Why do you need to do this?**
Before making changes to a project, you should install its dependencies so the code can run, and run the tests to make sure everything is working. This gives you a baseline to compare against after you make changes.

**Step 8a: Open the Terminal in VS Code**

1. In VS Code, open the integrated terminal:
   
   - Press ``Ctrl + ``` (backtick, the key below Escape) on Windows
   - Or press ``Command + ``` on Mac
   - Or go to **View** → **Terminal** in the menu

   .. note::
      [SCREENSHOT NEEDED: VS Code with the integrated terminal open at the bottom]

**Step 8b: Install Dependencies**

1. In the terminal, type the following command and press Enter:

   .. code-block:: bash

      uv sync

   This command reads the project's dependency file and installs all required libraries.

2. Wait for UV to download and install all dependencies. You'll see progress messages in the terminal.

   .. note::
      [SCREENSHOT NEEDED: VS Code terminal showing uv sync running and completing]

**Step 8c: Run the Tests**

1. In the terminal, type the following command and press Enter:

   .. code-block:: bash

      uv run pytest

   This runs all the tests in the project.

2. Look at the output. You should see something like:

   .. code-block:: text

      ==================== test session starts ====================
      collected X items

      tests/test_something.py ..F..

      ==================== 1 failed, X passed ====================

   - A dot (``.``) means a test passed
   - An ``F`` means a test failed

   .. note::
      [SCREENSHOT NEEDED: VS Code terminal showing pytest output with some failing tests]

3. If you see failing tests, don't worry! This is expected - your task is to fix them in the next step.


Step 9: Fix the Issue and Confirm It Works
==========================================

Now that you've set up the project and identified failing tests, it's time to fix the issue.

**Step 9a: Understand the Problem**

1. Look at the test output to see which tests are failing

2. The failing tests usually give you a clue about what's wrong. Look for:
   
   - The name of the failing test
   - The file and line number where the failure occurred
   - The expected value vs. the actual value

3. Open the relevant source code files to understand what the code is supposed to do

**Step 9b: Make Your Fix**

1. Navigate to the file that needs to be fixed using the file explorer on the left side of VS Code

2. Make the necessary changes to fix the issue

3. Save your file (``Ctrl + S`` on Windows, ``Command + S`` on Mac)

**Step 9c: Run the Tests Again**

1. In the terminal, run the tests again:

   .. code-block:: bash

      uv run pytest

2. Check if your fix worked:
   
   - If all tests pass (you see only dots, no ``F``), congratulations! Your fix worked!
   - If tests still fail, read the error messages, adjust your code, and try again

   .. note::
      [SCREENSHOT NEEDED: VS Code terminal showing pytest with all tests passing]

**Tip:** Run the tests frequently as you make changes. It's easier to fix problems when you've only made small changes.


Step 10: Add, Commit, and Push Your Changes
===========================================

**What is Add, Commit, and Push?**

- **Add (Stage)**: Tells Git which file changes you want to include in your next save point
- **Commit**: Creates a save point (snapshot) of your changes with a message describing what you did
- **Push**: Uploads your commits to GitHub so they're saved online and visible to others

**Why do you need to do this?**
This is how you save your work to GitHub. Without pushing, your changes only exist on your computer. Pushing ensures your work is backed up and can be submitted.

**Step 10a: Stage Your Changes**

1. In VS Code, click on the **Source Control** icon in the left sidebar (it looks like a branching line, and may show a number indicating changed files)

   .. note::
      [SCREENSHOT NEEDED: VS Code sidebar showing Source Control icon with changes indicator]

2. You'll see a list of files you've changed under "Changes"

3. Hover over the "Changes" header and click the **+** icon to stage all changes
   
   Or, hover over individual files and click the **+** icon next to each file to stage specific files

   .. note::
      [SCREENSHOT NEEDED: VS Code Source Control panel showing staged and unstaged changes]

**Step 10b: Commit Your Changes**

1. In the text box at the top of the Source Control panel, type a clear, descriptive message about what you changed. For example:
   
   - "Fix calculation error in get_total function"
   - "Add missing return statement"

2. Click the **Commit** button (checkmark icon) or press ``Ctrl + Enter`` (Windows) / ``Command + Enter`` (Mac)

   .. note::
      [SCREENSHOT NEEDED: VS Code Source Control showing commit message and Commit button]

**Step 10c: Push Your Changes to GitHub**

1. After committing, click the **Sync Changes** button that appears (or click the three dots menu and select **Push**)

   .. note::
      [SCREENSHOT NEEDED: VS Code showing the Sync Changes button after committing]

2. If this is your first time pushing, VS Code may ask you to log in to GitHub. Follow the prompts to authorize VS Code.

3. Wait for the push to complete. You'll see a notification when it's done.

**Verify your changes on GitHub:**

1. Go to your forked repository on GitHub (``https://github.com/YOUR-USERNAME/repository-name``)

2. You should see your recent commit message and the updated files

   .. note::
      [SCREENSHOT NEEDED: GitHub repository showing the recent commit]


Step 11: Enable and Check GitHub Actions
========================================

**What is GitHub Actions?**
GitHub Actions is GitHub's automation system. It can automatically run tests, check code quality, and perform other tasks whenever you push code.

**Why do you need to check it?**
Many projects use GitHub Actions to automatically run tests when you push changes. This gives you (and your instructor) confirmation that your code works correctly. When you fork a repository, Actions are disabled by default for security reasons, so you need to enable them.

**Step 11a: Enable GitHub Actions**

1. Go to your forked repository on GitHub

2. Click on the **Actions** tab at the top of the page

   .. note::
      [SCREENSHOT NEEDED: GitHub repository showing the Actions tab]

3. You'll see a message saying "Workflows aren't being run on this forked repository"

4. Click the green **"I understand my workflows, go ahead and enable them"** button

   .. note::
      [SCREENSHOT NEEDED: GitHub Actions page with the enable workflows button]

**Step 11b: Run the Workflow**

1. After enabling, you may need to trigger a workflow run. Some workflows run automatically on push; others need to be manually triggered.

2. If the workflow hasn't run automatically, you can trigger it:
   
   - Click on a workflow in the left sidebar
   - Click the **"Run workflow"** button on the right
   - Select the branch (usually ``main``) and click **"Run workflow"**

   .. note::
      [SCREENSHOT NEEDED: GitHub Actions showing Run workflow button]

**Step 11c: Check the Workflow Results**

1. After the workflow runs, you'll see a status indicator:
   
   - **Green checkmark** ✓ : All tests passed! Your code works correctly.
   - **Red X** ✗ : Something failed. Click on it to see what went wrong.

   .. note::
      [SCREENSHOT NEEDED: GitHub Actions showing workflow results]

2. If you see a failure, click on the failed workflow to see the details. Look for error messages that explain what went wrong.

3. If your tests fail on GitHub but passed locally, double-check:
   
   - Did you push all your changes?
   - Are there any differences between your local environment and the GitHub Actions environment?


Step 12: Apply for GitHub Student Developer Pack
================================================

**What is the GitHub Student Developer Pack?**
The GitHub Student Developer Pack is a collection of free tools and services for students. It includes free access to GitHub Copilot, cloud credits, domain names, and many other developer tools.

**Why should you apply?**
As a student, you get access to professional tools that would normally cost money. GitHub Copilot alone (which you set up in Step 6) normally costs $10/month, but it's free for students!

**How to Apply:**

1. Go to https://education.github.com/pack

2. Click the **"Sign up for Student Developer Pack"** button

   .. note::
      [SCREENSHOT NEEDED: GitHub Education page with the sign-up button]

3. Log in to your GitHub account if you haven't already

4. Select **"Student"** when asked about your academic status

5. Choose your school from the list (or type to search for it)

6. **Verify your student status** - you'll need to provide proof that you're a student. Options include:
   
   - Using your school email address (often ends in ``.edu``)
   - Uploading a photo of your student ID
   - Uploading other academic documents

   .. note::
      [SCREENSHOT NEEDED: GitHub Education verification page]

7. Submit your application

8. Wait for verification. This usually takes a few minutes to a few days, depending on the verification method.

9. Once approved, you'll receive an email confirming your access to the Student Developer Pack

**After You're Approved:**

- GitHub Copilot will become available (you may need to restart VS Code)
- Explore the other benefits at https://education.github.com/pack
- Your benefits last as long as you're a student, and you may need to re-verify periodically

.. note::
   If you're having trouble getting verified, try:
   
   - Using your official school email address
   - Making sure your student ID photo is clear and shows your name, the current date/semester, and your school's name
   - Waiting a few days and trying again if the automatic verification fails


Congratulations!
================

You've successfully set up your local Python development environment! You now have:

- ✅ Git for version control
- ✅ Python to run your code
- ✅ VS Code as your code editor
- ✅ The Python extension for VS Code features
- ✅ UV for managing Python packages
- ✅ GitHub Copilot for AI-assisted coding
- ✅ The skills to fork, clone, and work with repositories
- ✅ Knowledge of how to run tests and push changes
- ✅ Access to the GitHub Student Developer Pack

**What's Next?**

- Check out the :ref:`quickstart` to start building with Drafter
- Learn about :ref:`testing <testing-parts-of-routes>` your code
- When you're ready to share your project, see :ref:`deployment`

If you run into any problems, check the :ref:`help` page for common issues and solutions.
