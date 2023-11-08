# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'iguessthislldo'
author = 'Fred Hornsey'
github = 'https://github.com/iguessthislldo'
copyright = '2023, ' + author
pygments_style = 'manni'
nitpicky = True

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_design'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'output', 'input', '.venv']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo' # https://pradyunsg.me/furo/
html_title = project
html_sort_title = project
html_use_index = False
html_copy_source = False

html_static_path = ['_static', 'root']
html_extra_path = ['root']

html_theme_options = {
    'light_logo': 'logo-light.png',
    'dark_logo': 'logo-dark.png',
    'sidebar_hide_name': True, # Logo has the name in it
    'source_edit_link': github + '/blog/blob/master/docs/{filename}?plain=1',
    'light_css_variables': {
    },
    'dark_css_variables': {
        'color-brand-primary': '#00ff00',
    },
}

# Change the sidebar to include fixed links
#   https://pradyunsg.me/furo/customisation/sidebar/#making-changes
html_context = {
    'sidebar_links': {
        'GitHub': github,
    }
}
html_sidebars = {
    '**': [
        'sidebar/brand.html',
        'sidebar-links.html',
        'sidebar/search.html',
        'sidebar/scroll-start.html',
        'sidebar/navigation.html',
        'sidebar/ethical-ads.html',
        'sidebar/scroll-end.html',
        'sidebar/variant-selector.html',
    ]
}
