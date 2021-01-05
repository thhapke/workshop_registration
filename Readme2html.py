import markdown2
import re

html = markdown2.markdown_path('README.md')

# replace './static/' with ''
html = html.replace('./static/','/static/')

html_lines = html.split('\n')

li_0 = False
li_1 = False
count_p = 0
for i,line in enumerate(html_lines) :

    if not li_0 :
        count_p = count_p + line.count('<p>') -line.count('</p>')


    # no indent
    if re.match(r'\*\s+',line)  :
        line = re.sub(r'\*\s+','',line)
        line = re.sub('</p>', '', line)
        line = re.sub('<p>', '', line)

        line = '<li>' + line + '</li>'
        if not li_0 :
            li_0 = True
            line = '</p>'* count_p + '<ul>' + line
            count_p = 0
        elif li_1 :
            li_1 = False
            line = '</ul>' + line
        html_lines[i] = line
        print(html_lines[i])
    # with indent
    elif re.match(r'\s+\*\s+', line):
        line = re.sub(r'\s+\*\s+', '', line)
        line = '<li>' + line + '</li>'
        if not li_1 :
            li_1 = True
            line = '<ul>' + line
        html_lines[i] = line
        print(html_lines[i])
    else :
        if li_1 :
            line = line + '</ul></ul>'
            html_lines[i] = line
            li_1 = False
            li_0 = False
        elif li_0 :
            line = line + '</ul>'
            html_lines[i] = line
            li_0 = False

html = '\n'.join(html_lines)

html_header = """{% extends "baseadmin.html" %}
{% import "bootstrap/wtf.html" as wtf %}
{% block title %}Help{% endblock %}
{% block page_content %}
<div class="page-header">
    <h1>Documention </h1> </div>
<div class="text-body"> 
"""

html_end = '</div>\n{% endblock %}'

html = html_header + html + html_end

f = open('./templates/README.html','w')
f.write(html)
f.close()