#!/usr/bin/env python
# coding: utf8
from gluon import *
from gluon.globals import current
from gluon.dal import SQLDB, GQLDB, Row, Rows, Expression
from gluon.sqlhtml import represent
from gluon.html import BUTTON

from string import Template
import logging

import re
from html import truncate_string
table_field = re.compile('[\w_]+\.[\w_]+')
    

class Grid(object):
    """ This an example on how to make a grid to use with rawsql """
    
    template = '''function getData(grid_id, url, value, show_detail){
        $("#" + grid_id).load(url,{"avalue": value}, function(result) {
            if (show_detail == true) {
                 $("#$search_form_id").hide();
                 $("#$cancel_button_id").show();

            } else {
                 $("#$search_form_id").show();            
                 $("#$cancel_button_id").hide();
            }
        
        });
    }
    '''
    
    def __init__(self, 
                 db=None,
                 query=None, 
                 field_id=None,
                 fields=[], 
                 search_fields=[], 
                 rows_for_page=10, 
                 default_orderby=None, 
                 groupby=None, 
                 show_function=None,
                 search_function='list',
                 cid=None,
                 ui=None):
        """ Init """
        request = current.request

        self.db = db
        self.query = query
        self.field_id = fields[0]._table._id if not self.query else field_id
        self.fields = fields
        self.cid = None
        self.rows_for_page = rows_for_page
        self.rows_count = 0
        self.paginate = None
        self.default_orderby = str(default_orderby) if default_orderby else ""
        self.orderby = default_orderby
        self.groupby = groupby 
        self.next_orderby = ''
        self.search_string =''
        self.search_fields = search_fields
        self.ctrl = request.controller
        self.method = request.function
        self.grid_id = 'grid_' + self.method
        self.show_function = show_function
        self.search_function = search_function
        self.page = self.pages = 0
        self.rows = None
        self.cid = cid
        
        if not ui:
            self.ui = dict(
                paginator='pagination',
                paginatoractive='active',
                paginatornext='Next',
                paginatorprior='Prior',
                paginatorfirst='First',
                paginatorlast='Last'
            )
        else:
            self.ui = ui
        
        self.__get_args__()
        self.__get_rows__()
        self.grid = self.table(self.rows,
                                      columns=self.fields,
                                      headers='labels',
                                      cid=self.cid,
                                      renderstyle=False
                                      )
        

    def __call__(self):
        return DIV(self.pager(), self.table())

        
    def __get_args__(self):
        """"""
        request = current.request
        session = current.session        

        orderby_field = None

        session_orderby = session.get('%s_%s_%s' % (self.ctrl, self.method, 'last_orderby'))

        if request.cid:
            session['%s_%s_%s' % (self.ctrl, self.method, 'cid')] = request.cid
        else:
            self.cid = session['%s_%s_%s' % (self.ctrl, self.method, 'cid')]

        orderby = request.vars.get('orderby') or self.default_orderby
        self.search_string = request.vars.get('avalue') or ''

        self.next_orderby = orderby or ''
        if orderby and not isinstance(orderby, Expression):
            if session_orderby:
                if orderby.split('~')[-1] == session_orderby.split('~')[-1]:
                    self.next_orderby = orderby[1:] if orderby[0] == '~' else '~' + orderby
            else:                   
                self.next_orderby = orderby[1:] if orderby[0] == '~' else '~' + orderby

            if orderby.find('(') > -1:
                field = orderby
                table = orderby[orderby.find('(') + 1: -1].split('~')[-1].split('.')[0]
                self.orderby = Expression(self.db, orderby.split('~')[-1] )
            else:
                try:
                    table, field = orderby.split('~')[-1].split('.')
                    self.orderby= self.db[table][field]
                except:
                    pass
            
            if orderby[0] == '~':
                self.orderby = ~self.orderby
            session['%s_%s_%s' % (self.ctrl, self.method, 'last_orderby')] = orderby
        try:
            self.page = int(request.vars.page)
        except:
            self.page = 1
                                    

    def __get_rows__(self):
        """"""
        #from gluon import *
        db = self.db
        limit_inf = (self.rows_for_page * self.page) - self.rows_for_page
        limit_sup = limit_inf + self.rows_for_page
        qs = None
        if self.search_fields:
            for field in self.search_fields:
                if qs:
                    if self.search_string:
                        qs = qs | field.like('%' +  + '%')
                else:
                    if self.search_string:
                        qs = field.like('%' + self.search_string + '%')
            query = self.query & qs if self.query else qs
        else:
            query = self.query
            
        self.rows_count = len(db(query).select(*self.fields, groupby=self.groupby))
        if self.fields:
            self.rows = db(query).select(*self.fields, orderby=self.orderby, groupby=self.groupby, limitby=(limit_inf, limit_sup))

    
    def table(self, 
              *args,
              **attributes):
        self.cid = attributes['cid']
        request = current.request
        session = current.session
        attributes['_id'] = 'rawtable_' + self.method
            
        table = self.render_table(*args, **attributes) 
        grid = DIV(DIV(DIV(self.pager()), 
                       LABEL('Records found: %d' % self.rows_count)),
                   table, _class='web2py_grid ', _id='table_' + self.method)        
        
        div_basicgrid = DIV(grid, _id=self.grid_id)

        return div_basicgrid
    

    def render_table(self, 
              sqlrows,
              linkto=None,
              upload=None,
              orderby=True,
              headers={},
              truncate=16,
              th_link = '',
              columns=None,
              extracolumns=None,
              selectid=None,
              renderstyle=False,
              cid=None,
              **attributes):
        
        request = current.request
        
        attributes['_class'] = "table table-striped table-bordered table-condensed"
        if th_link == '':
            th_link=URL(self.ctrl, self.method)
            
        row = []    
        if not sqlrows:
            return DIV('', _class='web2py_table')
        if not columns:
            columns = sqlrows.colnames
        else:
            cols = columns[:]
            columns = []
            for c in cols:
                columns.append(str(c))
        if headers=='fieldname:capitalize':
            headers = {}
            for c in columns:
                headers[c] = c.split('.')[-1].replace('_',' ').title()
        elif headers=='labels':
            headers = {}
            for c in columns:
                if c.find('(') > -1:
                    headers[c] = c
                else:
                    (t,f) = c.split('.')
                    field = sqlrows.db[t][f]
                    headers[c] = field.label
        if headers is None:
            headers = {}
        else:
            for c in columns:#new implement dict
                if isinstance(headers.get(c, c), dict):
                    coldict = headers.get(c, c)
                    attrcol = dict()
                    if coldict['width']!="":
                        attrcol.update(_width=coldict['width'])
                    if coldict['class']!="":
                        attrcol.update(_class=coldict['class'])
                    row.append(TH(coldict['label'],**attrcol))
                elif orderby:
                    if self.next_orderby.split('~')[-1] == c:
                        u = self.next_orderby
                    else:
                        u = c
                    _href = th_link+'?orderby=' + u
                    if self.search_string != '':
                        _href = _href + '&search_string=' + self.search_string
                        
                    row.append(TH(A(headers.get(c, c), _href=_href, cid=cid)))
                else:
                    row.append(TH(headers.get(c, c)))
    
            if extracolumns:#new implement dict
                for c in extracolumns:
                    attrcol = dict()
                    if c['width']!="":
                        attrcol.update(_width=c['width'])
                    if c['class']!="":
                        attrcol.update(_class=c['class'])
                    row.append(TH(c['label'],**attrcol))
        
        thead = THEAD(TR(*row, _class=''))
        table = TABLE(thead, **attributes)
        
        tbody = []
        for (rc, record) in enumerate(sqlrows):
            row = []

            if not selectid is None: #new implement
                if record.get('id') == selectid:
                    _class += ' rowselected'

            for colname in columns:
                if not table_field.match(colname):
                    if "_extra" in record and colname in record._extra:
                        r = record._extra[colname]
                        row.append(TD(r))
                        continue
                    else:
                        raise KeyError("Column %s not found (SQLTABLE)" % colname)
                (tablename, fieldname) = colname.split('.')
                try:
                    field = sqlrows.db[tablename][fieldname]
                except KeyError:
                    field = None
                if tablename in record \
                        and isinstance(record, Row) \
                        and isinstance(record[tablename],Row):
                    r = record[tablename][fieldname]
                elif fieldname in record:
                    r = record[fieldname]
                else:
                    raise SyntaxError, 'something wrong in Rows object'
                r_old = r
                if not field:
                    pass
                elif linkto and field.type == 'id':
                    try:
                        href = linkto(r, 'table', tablename)
                    except TypeError:
                        href = '%s/%s/%s' % (linkto, tablename, r_old)
                    r = A(r, _href=href)
                elif isinstance(field.type, str) and field.type.startswith('reference'):
                    if linkto:
                        ref = field.type[10:]
                        try:
                            href = linkto(r, 'reference', ref)
                        except TypeError:
                            href = '%s/%s/%s' % (linkto, ref, r_old)
                            if ref.find('.') >= 0:
                                tref,fref = ref.split('.')
                                if hasattr(sqlrows.db[tref],'_primarykey'):
                                    href = '%s/%s?%s' % (linkto, tref, urllib.urlencode({fref:r}))
                        r = A(represent(field,r,record), _href=str(href))
                    elif field.represent:
                        r = represent(field,r,record)
                elif linkto and hasattr(field._table,'_primarykey')\
                        and fieldname in field._table._primarykey:
                    # have to test this with multi-key tables
                    key = urllib.urlencode(dict( [ \
                                ((tablename in record \
                                      and isinstance(record, Row) \
                                      and isinstance(record[tablename], Row)) and
                                 (k, record[tablename][k])) or (k, record[k]) \
                                    for k in field._table._primarykey ] ))
                    r = A(r, _href='%s/%s?%s' % (linkto, tablename, key))
                elif isinstance(field.type, str) and field.type.startswith('list:'):
                    r = represent(field,r or [],record)
                elif field.represent:
                    r = represent(field,r,record)
                elif field.type == 'blob' and r:
                    r = 'DATA'
                elif field.type == 'boolean':
                    r = INPUT(_type='checkbox', value=r, _disabled='')                   
                elif field.type == 'upload':
                    if upload and r:
                        r = A(current.T('file'), _href='%s/%s' % (upload, r))
                    elif r:
                        r = current.T('file')
                    else:
                        r = ''
                elif field.type in ['string','text']:
                    r = str(field.formatter(r))
                    if headers!={}: #new implement dict
                        if isinstance(headers[colname],dict):
                            if isinstance(headers[colname]['truncate'], int):
                                r = truncate_string(r, headers[colname]['truncate'])
                    elif not truncate is None:
                        r = truncate_string(r, truncate)
                attrcol = dict()#new implement dict
                if headers!={}:
                    if isinstance(headers[colname],dict):
                        colclass=headers[colname]['class']
                        if headers[colname]['selected']:
                            colclass= str(headers[colname]['class'] + " colselected").strip()
                        if colclass!="":
                            attrcol.update(_class=colclass)

                row.append(TD(r,**attrcol))

            if extracolumns:#new implement dict
                for c in extracolumns:
                    attrcol = dict()
                    colclass=c['class']
                    if c['selected']:
                        colclass= str(c['class'] + " colselected").strip()
                    if colclass!="":
                        attrcol.update(_class=colclass)
                    contentfunc = c['content']
                    row.append(TD(contentfunc(record, rc),**attrcol))
                
            if self.show_function:
                tbody.append(TR(*row, 
                                _id='%s_%s_row_%d' % (self.ctrl, self.method, record[self.field_id]),
                                _onclick='getData("%(grid_id)s", "%(url)s", %(value)s, %(detail)s); return false;' %
                                {'grid_id': self.grid_id, 
                                 'url': URL(r=request, f=self.show_function, extension='load'),
                                 'value': str(record[self.field_id]),
                                 'detail': 'true'}
                            ))
            else:
                tbody.append(TR(*row, _id='%s_%s_row_%d' % (self.ctrl, self.method, record[self.field_id])))
        table.append(TBODY(*tbody))        

        return DIV(table, _class='web2py_table')
        

    def pager(self):
        """Paginate"""

        request = current.request

        paginator = UL()
        ui = self.ui

        if self.rows_for_page < self.rows_count:
            npages, reminder = divmod(self.rows_count, self.rows_for_page)
            if reminder: npages += 1
            try: page = int(request.vars.page or 1) - 1
            except ValueError: page = 0

            NPAGES = 5 # window is 2*NPAGES
            if page > NPAGES+1:
                paginator.append(LI(self.page_link(ui.get('paginatorfirst', '<<'), 0)))

            if page > NPAGES:
                paginator.append(LI(self.page_link(ui.get('paginatorprior', '<'), page - 1)))

            pages = range(max(0, page - NPAGES), min(page + NPAGES, npages))
            for p in pages:
                if p == page:
                    paginator.append(LI(A(p+1, _onclick='return false'),
                        _class=ui.get('paginatoractive', '')))
                else:
                    paginator.append(LI(self.page_link(p+1, p)))

            if page < npages - NPAGES:
                paginator.append(LI(self.page_link(ui.get('paginatornext', '>'), page + 1)))

            if page < npages - NPAGES-1:
                paginator.append(LI(self.page_link(ui.get('paginatorlast', '>>'), npages - 1)))
                
            p = DIV(paginator, _class=ui.get('paginator'))
        else:
            p = DIV()            
            
        return p
    
    def page_link(self, name, page):
        request = current.request

        argss = request.args
        varss = request.vars

        varss['page'] = page + 1
        page_url = URL(args=argss, vars=varss)

        return A(name, _href=page_url, cid=self.cid)    
    
    @staticmethod
    def render_search(show_function='show', search_function='list'):
        """search"""

        request = current.request
        id_search_form = '%s_%s_searchform' % (request.controller, request.function)
        id_cancelbutton = '%s_%s_cancelbutton' % (request.controller, request.function)
        label = ""#LABEL('Search: ')
        search = INPUT(_type='text', _value="", _placeholder="Search", _class="search-query", 
                       _onkeyup='getData("%(grid_id)s", "%(url)s", this.value, false); return false;' %
                       {'grid_id': 'grid_' +  search_function, 
                        'url': URL(r=request, f=search_function, extension='load')})
        search_form = DIV(DIV(
            Grid.script(show_function=show_function, search_function=search_function), 
            DIV(label, search, _class='form-search'),
            _id=id_search_form),
            BUTTON('Elenco',
                   _onclick='getData("%(grid_id)s", "%(url)s", %(value)s, false); return false;' %
                   {'grid_id': 'grid_' +  search_function, 
                    'url': URL(r=request, f=search_function, extension='load'),
                    'value': '$("#%s input.search-query").val()' % id_search_form},
                   _id=id_cancelbutton, _style='display:none;'),
            HR(),
        )
        
        return search_form
    
    @staticmethod
    def script(show_function='show', search_function='list'):
        request = current.request
        script_dict = {'show_url': URL(r=request, f=show_function, extension='load'),
                       'search_url': URL(r=request, f=search_function, extension='load'),
                       'grid_id': 'grid_' + search_function,
                       'search_form_id': '%s_%s_searchform' % (request.controller, request.function),
                       'cancel_button_id': '%s_%s_cancelbutton' % (request.controller, request.function),
                       }
        
        return SCRIPT(Template(Grid.template).safe_substitute(script_dict))
    
