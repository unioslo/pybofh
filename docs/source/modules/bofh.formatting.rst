bofh.formatting
===============

The formatting module consists of utilities for displaying responses from the
XMLRPC server in a human readable form.

Most notably is the parsing and formatting according to the hints (format
suggestions) given by the server.

Not all commands will have format suggestions. An XMLRPC command will either:

- Not use format suggestions and return a pre-formatted string
- Use format suggestions and return a dictionary or list of dictionaries.

For commands with format suggestions, the formatting class
:py:class:`SuggestionFormatter` is used. For all other commands,
:py:class:`StringFormatter` is used.


Format suggestions
------------------
A format suggestion is a dictionary with the following keys and values:

hdr
    An optional header line (string)

str_vars
    Either a string, a tuple or a list of tuples.

    If str_vars is **a string**, it will be outputted directly.

    If str_vars is **a tuple**, it should contain two or three items:

    1. A format string (e.g. "foo=%s, bar=%s")
    2. A list of references to keys in the bofh response to use for formatting
       the string (e.g. ['foo_value', 'bar_value'])
    3. An optional sub header

    If str_vars is **a list of tuples**, each tuple should be on the format
    mentioned. Each tuple is only formatted and added to the output if the keys
    in the tuple exists in the bofh response.


Format suggestions can be parsed and turned into :py:class:`FormatSuggestion`
objects by running :py:meth:`FormatSuggestion.from_dict` on the format
suggestion dict from the server.

FormatSuggestion objects are a collection of :py:class:`FormatItem` objects.
Each FormatItem object represents one (format string, keys, sub header) tuple
within the format suggestion. Each FormatItem object typically has one or more
:py:class:`FieldRef` objects.


Example
-------

Let's assume that the server responds with the following format suggestion dict
for a given command:

.. code:: python

    {'str_vars': [
         ("name: %s", ('name',)),
         ("pos:  %d,%d", ('x', 'y')),
         ("size: %d by %d", ('width', 'height')), ]}


If a call to the command returns:

.. code:: python

    {'name': 'foo', 'x': 50, 'y': 100, 'width': 10, 'height': 20}

Then the result of using the format suggestion to print the result, should
output:

.. code:: text

    name: foo
    pos:  50,100
    size: 10 by 20

If either 'x' or 'y' is missing in a response, the second line should *not* be
printed -- *all* the listed references in each str_vars tuple *must* be present
for the format suggestion to be printed.

Note a response may contain multiple dicts too. The response:

.. code:: python

    [
      {'name': 'foo', 'width': 10, 'height': 20},
      {'name': 'bar', 'x': 70, 'y': 100},
    ]

Should result in:

.. code:: text

    name: foo
    size: 10 by 20
    name: bar
    pos: 70,100


.. automodule:: bofh.formatting
   :members:
