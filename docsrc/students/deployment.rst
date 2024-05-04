.. _deployment:

Deployment
==========

When you have finished developing your website, you can deploy it to the world on a server.
GitHub Pages is a free and easy way to host your website.
Although normally Github Pages is only useful for hosting frontend websites, Drafter can still work with it.

To deploy your website to GitHub Pages, you need to follow these steps:

Create the Repository
---------------------

1. Use the URL provided by your instructor to create a new repository on Github (**Make sure you use the instructor provided URL for your classroom!**)

Once the repository is created, you will see that there are already a bunch of files present, and a settings bar.

.. image:: images/deployment_github_main.png
    :alt: Github Repository

Enable Github Pages
-------------------

2. You will need to turn on GitHub pages in order to host your site. To do this, go to the ``Settings`` tab of your repository.

.. image:: images/deployment_github_settings.png
    :alt: Github Settings

Scroll down to the ``Pages`` section on the left side of the page. Under the source dropdown, select ``Github Actions``.

.. image:: images/deployment_github_pages.png
    :alt: Github Pages

Your site will now start deploying whenever you make a change. We can check the progress of the deployment by going to the ``Actions`` tab. But first, we'll need to upload our website code.

Upload Your Website Code
------------------------

3. Go to the ``Code`` tab and click on the ``website`` folder.

.. image:: images/deployment_github_code.png
    :alt: Github Code

There will be one file by default in the folder, ``main.py``. You can add other files to this folder, and they will be available on your website. However, we must have a ``main.py`` file, which is where the main code for your site should go. Click on the file.

.. image:: images/deployment_github_files.png
    :alt: Github Files

When you click on the file, it will show you the contents of the file. You can edit the file by clicking on the pencil icon.

.. image:: images/deployment_github_edit.png
    :alt: Github Edit Main

The editor area allows you to paste in your code. We recommend that you add the following lines of code to your project.

.. code-block:: python

    hide_debug_information()
    set_website_title("Your Website Title")
    set_website_framed(False)

These lines of code:

1. Hide all of the debug information
2. Set the title of the website in the tab
3. Make the website stretch to fill the whole screen, instead of just the small box.

There are many other ways to style your website, but these are a starting point.

When you are done, click on the ``Commit changes`` button in the top-right of the page.

.. image:: images/deployment_github_editor.png
    :alt: Github Editor

A box will appear that asks you to write a commit message. This is a message that describes the changes you made to the file. You can write anything you want here, but it is recommended to write something that describes the changes you made.
Even if you just leave the default message, you must click on the ``Commit changes`` button to save your changes.

.. image:: images/deployment_github_commit.png
    :alt: Github Commit

Edit the Readme
---------------

4. Now we need to edit your ``readme.md`` file to update the information about your website. Click on the ``readme.md`` file in the ``website`` folder.

.. image:: images/deployment_github_readme.png
    :alt: Github Readme

Click on the pencil icon to edit the file. You will need to fill in the following fields.

* The name of your site
* What your web application does
* Your name and UD email address
* If you got significant help from a website besides the official Drafter documentation, include links along with explanations of how the site helped you. If someone helped you, this is also a nice place to mention them to thank them for their help.
* The planning document that you created, provided as a file (see below).
* The URL (address) of the publicly-accessible video (described below) that you uploaded.

.. image:: images/deployment_github_editme.png
    :alt: Github Readme

Record a Video
--------------

5. Record a video of your web application running, and make sure you show and address all of the following with a voiceover:

* What your web application does
* What each page of your website looks like in action (i.e., walk through the website)
* What the state of your website looks (i.e., explain the fields of your State dataclass)
* Make sure that your video is audible and visible. If we cannot see parts or hear parts, we will treat that those parts as if they do not exist.

You do not need to walk through any of the code of your website, but we do want to see all of its features.

Aim for a video that is 2-5 minutes in length. Do not pad with unnecessary details, but do not skip important parts.

Think of this video as something you will want to put into a portfolio when you apply for internships and jobs. Try to do a good job.

Zoom can be used to record videos; again, just make sure that we are able to see and hear everything clearly.

Upload the video to a website where it can be viewed by the graders, and include the link to the video in both the docstring of the Python file and in the text entry box here.

Upload the Planning Document
----------------------------

6. Upload your planning document to the website repository in the ``website`` folder. You can do this by clicking on the ``Add file`` button and selecting the file from your computer.

Change the filename of the planning document to something simple and easy to type. You will need to link it in your ``readme.md` file.

View the Deployment
-------------------

7. When everything is done, you can check out your deployed website. Click on the ``Actions`` link to see the deployments. You can click on the latest deployment to see the logs.

.. image:: images/deployment_github_actions.png
    :alt: Github Actions

If everything is successful, you will see a green checkmark. You can click on the link to see your website.

.. image:: images/deployment_github_success.png
    :alt: Github Success

If you see a red X, there was an error. You can click on the error to see what went wrong.

.. image:: images/deployment_github_error.png
    :alt: Github Error

If you see an error, you can try to fix it and push the changes to the repository. The website will automatically update when you push changes to the repository.

Submit on Canvas
----------------

8. Once you have successfully deployed your website, you can submit the URL of your website to the assignment on Canvas.

