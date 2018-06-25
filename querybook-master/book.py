#coding:utf-8
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import webbrowser

from SPARQLWrapper import SPARQLWrapper, JSON

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

bootstrap = Bootstrap(app)
moment = Moment(app)


class NameForm(FlaskForm):
    name = StringField('Which book are you want to know?', validators=[DataRequired()])
    submit = SubmitField('Submit')


def booksInformation(title_name):
    '''
    sparql语句在http://dbpedia.org/sparql中查询想要书籍的信息。
    :param title_name:
    :return:
    '''

    str_ql = 'FILTER((LANG(?title) = "en") && (regex(?title,"'+title_name+'"))).'
    sparql = SPARQLWrapper('http://dbpedia.org/sparql')

    sparql.setQuery('''
PREFIX : <http://dbpedia.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT  ?thumbnail ?title ?author_name ?abstrct ?language ?country ?publisher ?translator 
FROM <http://dbpedia.org/>
WHERE {

?author rdf:type dbo:Writer .
?author rdfs:label ?author_name 
FILTER (LANG(?author_name)="en").

?author dbo:notableWork ?work .
?work rdfs:label ?title .'''
+ str_ql +
'''
?work rdfs:label ?title ;
dbo:abstract ?abstrct .
FILTER (LANG(?abstrct)="en").

OPTIONAL {?work dbp:language ?language.}
OPTIONAL {?work dbp:country ?country.}
OPTIONAL {?work dc:publisher ?publisher.}
OPTIONAL {?work dbo:translator ?translator.}
OPTIONAL {?work dbo:thumbnail ?thumbnail.}

} LIMIT 100
''')

    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
    except:
        open('./information_error.txt').write('The query fails \n ')
    else:
        # 解析结果在网页上显示
        # Create HTML output
        fs = open('./booksInformation.html', 'w')
        fs.write('<html><head><title>Information about the book </head></title>\n')

        fs.write('<boby>\n<ul>\n')
        fs.write('<h1><center>Information about the book </h1>')
        str = '<a href="{}"><center><h2><b>{}</b></h2></a><img src= "{}" height="60px"> <table width="100%" border="1"><col align="left" /><col align="left" /><col align="right" /> \
        <tr><th>language</th><th>country</th><th>publisher</th><th>translator</th></tr>\
        <tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr></table>\
        <li><b>{}</b><br> {} <br></li>'
        for result in results['results']['bindings']:
            if ('title' in result):
                # Create Wikipedia Link
                url = 'http://en.wikipedia.org/wiki/' + result['title']['value'].replace(' ', '_')
                title = result['title']['value']
            else:
                title = 'NONE'
            if ('author_name' in result):
                author_name = result['author_name']['value']
            else:
                author_name = 'NONE'
            if ('abstrct' in result):
                abstrct = result['abstrct']['value']
            else:
                abstrct = 'NONE'
            if ('language' in result):
                language = result['language']['value']
            else:
                language = 'NONE'
            if ('country' in result):
                country = result['country']['value']
            else:
                country = 'NONE'
            if ('publisher' in result):
                publisher = result['publisher']['value']
            else:
                publisher = 'NONE'
            if ('translator' in result):
                translator = result['translator']['value']
            else:
                translator = 'NONE'
            if ('thumbnail' in result):
                pic = result['thumbnail']['value']
            else:
                pic = 'http://upload.wikimedia.org/wikipedia/commons/7/7a/Question_Mark.gif'

            fs.write(str.format(  url,title,pic.replace('300px', '60px'), language, country, publisher, translator,author_name,  abstrct,))
        fs.write('</ul>\n')
        fs.write('</boby></html>')
        fs.close()


def recommendedBooks(title_name):
    #替换书名中的空格为/
    str = title_name
    str = str.replace(' ','_')
    str_book = 'dbr:'+str
    str_ql = 'FILTER (?book!= '+str_book+').'
    sparql = SPARQLWrapper('http://dbpedia.org/sparql')
    #搜索一部相似的书籍，做推荐
    sparql.setQuery(
        '''
        SELECT COUNT(?book) SAMPLE(?book)
        FROM <http://en.dbpedia.org>
        WHERE
        {
        '''
         + str_book +

         '''
        rdf:type ?o.
        ?book rdf:type ?o
        '''
         + str_ql +

         '''
        }GROUP BY ?book
        ORDER BY DESC(COUNT(?book))
        '''
        )

    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
    except:
        open('./recommended_error.txt').write('The query fails \n ')
    else:
        # 解析结果在网页上显示
        # Create HTML output
        fs = open('./recommendedBooks.html', 'w', encoding = 'utf-8')
        fs.write('<html><head><title>Recommended books</head></title>\n')

        fs.write('<boby>\n<ul>\n')
        fs.write('<table width="100%" border="1"><col align="left" /><col align="left" /><col align="right" /> \
        <tr><th>Recommended Books</th></tr>')
        str = '<tr><td><a href="{}">{}</a></td></tr>'
        for result in results['results']['bindings']:
            if ('callret-1' in result):
                callret1 = result['callret-1']['value']
            else:
                callret1 = 'NONE'
            fs.write(str.format(callret1,callret1))
        fs.write('</table>\n</ul>\n')
        fs.write('</boby></html>')
        fs.close()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    name = None
    form = NameForm()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        #通过sparql查询书籍相关信息
        booksInformation(name)
        #推荐类似书籍
        recommendedBooks(name)
        webbrowser.open(r".\booksInformation.html")
        webbrowser.open(r".\recommendedBooks.html")
    return render_template('index.html', form=form, name=name)

if __name__ == '__main__':
    app.run()
