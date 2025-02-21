from drafter import route, start_server, Page, TextArea, Button, assert_equal


@route("index")
def index():
    return Page(None, [
        "Let's write some HTML.",
        "<strong>This is a test.</strong>",
        'He said, "These are some quotes.".',
        "What happens if I put a < in here?",
        "And a > here?",
        "What happens if they embed entities in here?",
        Button("This ' apostrophe and & might cause trouble.", index)
    ])


assert_equal(
 index(),
 Page(state=None,
      content=["Let's write some HTML.",
              '<strong>This isa test.</strong>',
              'He said, "These are some quotes.".',
              'What happens if I put a < in here?',
              'And a > here?',
              'What happens if they embed entities in here?',
              Button(text="This ' apostrophe and & might cause trouble.", url='/')]))

start_server(cdn_skulpt="http://localhost:63342/skulpt/dist/skulpt.js",
             cdn_skulpt_std="http://localhost:63342/skulpt/dist/skulpt-stdlib.js",
             cdn_skulpt_drafter="http://localhost:8000/skulpt-drafter.js")