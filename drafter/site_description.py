from typing import Optional, Union, Dict, Any
from datetime import datetime
from drafter.page import Page
from drafter.routes import route


def site_description(
    title: str,
    description: str,
    author: Optional[str] = None,
    contact_email: Optional[str] = None,
    creation_date: Optional[Union[str, datetime]] = None,
    version: Optional[str] = None,
    url: str = "about",
    **additional_metadata: Any
) -> None:
    """
    Creates an "about" page for the site with metadata information.
    
    This function automatically creates a route for an "about" page that displays
    site information including title, description, author, and other metadata.
    This is intended to replace the need for students to create separate Markdown files.
    
    :param title: The title of the website/project
    :param description: A description of what the website/project does
    :param author: The name of the person/people who created the site
    :param contact_email: Contact email for the site
    :param creation_date: When the site was created (string or datetime object)
    :param version: Version number of the site/project
    :param url: The URL path for the about page (defaults to "about")
    :param additional_metadata: Any additional key-value pairs to display
    """
    
    def about_page() -> Page:
        """
        The actual page function that gets routed to the about URL.
        """
        content = []
        
        # Add title
        content.append(f"<h1>{title}</h1>")
        
        # Add description
        content.append(f"<p><strong>Description:</strong> {description}</p>")
        
        # Add author if provided
        if author:
            content.append(f"<p><strong>Author:</strong> {author}</p>")
        
        # Add contact email if provided
        if contact_email:
            content.append(f"<p><strong>Contact:</strong> <a href='mailto:{contact_email}'>{contact_email}</a></p>")
        
        # Add creation date if provided
        if creation_date:
            if isinstance(creation_date, datetime):
                date_str = creation_date.strftime("%B %d, %Y")
            else:
                date_str = str(creation_date)
            content.append(f"<p><strong>Created:</strong> {date_str}</p>")
        
        # Add version if provided
        if version:
            content.append(f"<p><strong>Version:</strong> {version}</p>")
        
        # Add any additional metadata
        if additional_metadata:
            content.append("<h2>Additional Information</h2>")
            for key, value in additional_metadata.items():
                # Convert underscores to spaces and capitalize for display
                display_key = key.replace('_', ' ').title()
                content.append(f"<p><strong>{display_key}:</strong> {value}</p>")
        
        return Page(content)
    
    # Register the route
    route(url)(about_page)