:tags: apache, webdev
:created: 2016-08-03T00:00:00+00:00
:published: 2016-08-03T00:00:00+00:00
:summary: Rambling about an experience with configuring Apache

#############################
Apache vhosts and Redirecting
#############################

.. post-info-start

.. card::

    :material-regular:`calendar_month` 2016-08-03
    :material-regular:`sell` :bdg-ref-primary-line:`apache <tag-apache>` :bdg-ref-primary-line:`webdev <tag-webdev>`


.. post-info-end

When using Apache's `virtual hosts <https://httpd.apache.org/docs/current/vhosts/>`__ for the first time it can be easy (at least for me) to make mistake(s) trying to get it a very specific way.
For me that specific way was as follows:

- Have a main host that lives on a subdomain (this site BTW) that only accepts https.
- By default, anything else redirects to the main site...
- Except for other virtual hosts

This might seem simple if you a little bit about virtual hosts, which I thought I did before setting this site up.
However, the problem I had today was that I kept either getting forbidden responses or redirected to another other virtual host (Not the one I wanted).
Below is the gist of my working ``000-default.conf``` as of writing:

.. code-block:: apache
    :linenos:
    :caption: Something

    <VirtualHost *:80>
        ServerAdmin subdomain@domain.tld

        # Logging
        # Rename these if you have or own scheme or remove them to log to the default files
        LogLevel warn
        ErrorLog    ${APACHE_LOG_DIR}/default_redirect_error.log
        CustomLog   ${APACHE_LOG_DIR}/default_redirect_access.log combined

        # Redirect to https://subdomain.domain.tld/
        RewriteEngine on
        RewriteRule "^/?(.*)"      "https://subdomain.domain.tld/$1" [L,R,NE]
    </VirtualHost>

    # HTTPS
    <IfModule mod_ssl.c>
    <VirtualHost *:443>
        ServerAdmin subdomain@domain.tld

        # Logging
        # Rename these if you have or own scheme or remove them to log to the default files
        LogLevel warn
        ErrorLog    ${APACHE_LOG_DIR}/default_redirect_error.log
        CustomLog   ${APACHE_LOG_DIR}/default_redirect_access.log combined

        # SSL Stuff Goes here
        # I'm not completely sure this entire virtual host is necessary, but I decided to leave it

        # Redirect to https://subdomain.domain.tld/
        RewriteEngine on
        RewriteRule "^/?(.*)"      "https://subdomain.domain.tld/$1" [L,R,NE]
    </VirtualHost>
    </IfModule>

I was having problems at first because I wasn't even using ``000-default.conf`` as a name, just the domain name.
If Apache is configured to use ``sites-available`` and ``sites-enabled`` it loads them alphabetically (I guess?).
Any way the first virtual host on the first config file loaded is the "default" one.

I was still having problems though, and even though I left directives like ``<DocumentRoot "/var/www/...">`` and ``<ServerAlias domain.tld>`` in there what finally fixed redirecting from the root domain to the subdomain was changing ``<VirtualHost *:*>`` to ``<VirtualHost *:80>``.

This was throwing me off because the line is `on the Apache website <https://httpd.apache.org/docs/current/vhosts/examples.html#proxy>`__ but doesn't produce the result I thought it would: catching everything that was not port 443 or the other virtual hosts.
This is made clear if you run ``apachectl -S``, which prints the current configuration, and is great for debugging the virtual hosts because it lists them in order of precedence.
