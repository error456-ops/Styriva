from django import template

register = template.Library()


@register.filter
def cl_opt(url, params="f_auto,q_auto,w_800"):
    """Add Cloudinary transformations (resize / compress) to an image URL."""
    url = str(url or "")
    marker = "/upload/"
    if marker not in url:
        return url
    return url.replace(marker, f"/upload/{params}/", 1)


@register.filter
def cl_download(url):
    """Make a Cloudinary URL download as a file instead of opening in the browser."""
    return cl_opt(url, "fl_attachment")