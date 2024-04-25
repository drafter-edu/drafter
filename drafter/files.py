import gzip
import base64

BASIC_SCRIPTS = "<script>" + """
    let snippets = document.getElementsByClassName('copyable');
    const buttonText = "📋";
    console.log(snippets);
    for (let i = 0; i < snippets.length; i++) {
        code = snippets[i].textContent;
        //snippets[i].classList.add('hljs'); // append copy button to pre tag
        snippets[i].innerHTML = '<button class="copy-button">'+buttonText+'</button>' + snippets[i].innerHTML; // append copy button
        snippets[i].getElementsByClassName("copy-button")[0].addEventListener("click", function () {
            this.innerText = 'Copying..';
            navigator.clipboard.writeText(code);
            this.innerText = 'Copied!';
            button = this;
            setTimeout(function () {
                button.innerText = buttonText;
            }, 1000)
        });
    }
""" + "</script>"
BASIC_STYLE = """
<style>
    div.btlw-debug .copy-button {
         float: right;
         cursor: pointer;
         background-color: white;
         padding: 4px;
     }

    div.btlw-container {
        padding: 1em;
        border: 1px solid lightgrey;
    }

    div.btlw-header {
        border: 1px solid lightgrey;
        border-bottom: 0px;
        background-color: #EEE;
        padding-left: 1em;
        font-weight: bold;
    }

    div.btlw-container img {
        display: block;
    }
</style>
"""
SKELETON_COMPRESSED = "<style>" + gzip.decompress(base64.b64decode(
    "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")).decode('utf-8') + "</style>"

DIFF_STYLE_TAG = """
<style type="text/css">
    table.diff {
        font-family:Courier,serif;
        border:medium;
        margin-bottom: 4em;
        width: 100%;
    }
    .diff_header {background-color:#e0e0e0}
    td.diff_header { text-align:right; }
    table.diff td {
        padding: 0px;
        border-bottom: 0px solid black;
    }
    .diff_next {background-color:#c0c0c0}
    .diff_add {background-color:#aaffaa}
    .diff_chg {background-color:#ffff77}
    .diff_sub {background-color:#ffaaaa}
</style>
"""

INCLUDE_STYLES = {
    'bootstrap': {
        'styles': [
            BASIC_STYLE,
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" integrity="sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65" crossorigin="anonymous">',
            DIFF_STYLE_TAG,
        ],
        'scripts': [
            '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-kenU1KFdBIe4zVF0s0G1M5b4hcpxyD9F7jL+jjXkk+Q2h455rYXK/7HAuoJl+0I4" crossorigin="anonymous"></script>',
            '<script src="https://code.jquery.com/jquery-3.7.1.slim.min.js" integrity="sha256-kmHvs0B+OpCW5GVHUNjv9rOmY0IvSIRcf7zGUDTDQM8=" crossorigin="anonymous"></script>',
            BASIC_SCRIPTS,
        ]
    },
    "skeleton": {
        "styles": [
            SKELETON_COMPRESSED,
            BASIC_STYLE,
            DIFF_STYLE_TAG,
        ],
        "scripts": [BASIC_SCRIPTS, ]
    },
    "skeleton_cdn": {
        "styles": [
            BASIC_STYLE,
            '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css" integrity="sha512-EZLkOqwILORob+p0BXZc+Vm3RgJBOe1Iq/0fiI7r/wJgzOFZMlsqTa29UEl6v6U6gsV4uIpsNZoV32YZqrCRCQ==" crossorigin="anonymous" referrerpolicy="no-referrer" />',
            DIFF_STYLE_TAG,
        ],
        "scripts": [BASIC_SCRIPTS, ]
    },
    'none': {
        'styles': [BASIC_STYLE, DIFF_STYLE_TAG],
        'scripts': [BASIC_SCRIPTS, ]
    }
}

TEMPLATE_200 = """
"""
TEMPLATE_404 = """
<style type="text/css">
  .btlw {{background-color: #eee; font-family: sans-serif;}}
  div.btlw {{background-color: #fff; border: 1px solid #ddd;
        padding: 15px; margin: 15px;}}
  .btlw pre {{background-color: #eee; border: 1px solid #ddd; padding: 5px;}}
</style>
<h3>{title}</h3>

<p>{message}</p>

<p>Original error message:</p>
<pre>{error}</pre>

<p>Available routes:</p>
{routes}
"""
TEMPLATE_500 = """
<style type="text/css">
  .btlw {{background-color: #eee; font-family: sans-serif;}}
  div.btlw {{background-color: #fff; border: 1px solid #ddd;
        padding: 15px; margin: 15px;}}
  .btlw pre {{background-color: #eee; border: 1px solid #ddd; padding: 5px;}}
</style>
<h3>{title}</h3>

<p>{message}</p>

<p>Original error message:</p>
<pre>{error}</pre>

<p>Available routes:</p>
{routes}
"""
