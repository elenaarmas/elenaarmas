#!/bin/bash

# Fix WordPress relative paths in HTML files using fd and sed
fd index.html -x sed -i \
    -e 's/href="wp-/href="\/wp-/g' \
    -e 's/src="wp-/src="\/wp-/g' \
    -e 's/url(wp-/url(\/wp-/g'
