import shutil

source_css = 'static\pretty.css'
destination_css = 'antenv/lib/python3.10/site-packages/docutils/writers/s5_html/themes/default/pretty.css'

shutil.copy(source_css, destination_css)


