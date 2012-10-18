#!/usr/bin/env python
# coding: utf8
from gluon import *
from gluon.globals import current
from dal import SQLDB, GQLDB
from gluon.dal import Row, Rows, Expression
from gluon.sqlhtml import represent

import re
from html import truncate_string
table_field = re.compile('[\w_]+\.[\w_]+')

if current.request.is_local: 
    from gluon.custom_import import track_changes 
    track_changes()
    
class BasicGrid(object):
    """ This an example on how to make a grid to use with rawsql """

    def __init__(self, db, ctrl, method, rows_per_page=10, default_orderby=None, ui=None):
        """ Init """

        self.db = db
        self.cid = None
        self.rows_per_page = rows_per_page
        self.rows_count = 0
        self.paginate = None
        self.default_orderby = default_orderby
        self.next_orderby = ''
        self.search_string=''
        self.ctrl = ctrl
        self.method = method
        self.grid_id = 'grid_' + self.method

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
        
        self.__helper__()
    #----------------------------------------------------------------------
    def __helper__(self):
        """"""
          
        orderby_field = None
        request = current.request
        session = current.session        

        session_orderby = session.get('%s_%s_%s' % (self.ctrl, self.method, 'last_orderby'))
        if request.cid:
            session['%s_%s_%s' % (self.ctrl, self.method, 'cid')] = request.cid

        orderby = request.vars.get('orderby') or self.default_orderby
        self.search_string = request.vars.get('search_string') or ''

        self.next_orderby = orderby or ''
        if orderby:
            if session_orderby:
                if orderby.split('~')[-1] == session_orderby.split('~')[-1]:
                    self.next_orderby = orderby[1:] if orderby[0] == '~' else '~' + orderby
            else:                   
                self.next_orderby = orderby[1:] if orderby[0] == '~' else '~' + orderby
                        
            session['%s_%s_%s' % (self.ctrl, self.method, 'last_orderby')] = orderby
            table, field = orderby.split('~')[-1].split('.')
            try:
                orderby_field = self.db[table][field]
            except:
                orderby_field = Expression(self.db, orderby.split('~')[-1])
        try:
            page = int(request.vars.page)
        except:
            page = 1
                                    
        self.helper = dict(orderby=orderby_field, page=page, search_string=self.search_string)
           
    
    def table(self, 
              *args,
              **attributes):
        #self.cid = attributes['cid'] or ''
        request = current.request
        session = current.session
        attributes['_id'] = 'rawtable_' + self.method
            
        table = self.render_table(*args, **attributes) 
        grid = DIV(DIV(DIV(self.render_paginate()), 
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
        attributes['_class'] = "table table-striped table-bordered table-condensed"
        if th_link == '':
            th_link=URL(self.ctrl, self.method)
            
        row = []    
        if not sqlrows:
            return DIV('', _class='web2py_table')
        if not columns:
            columns = sqlrows.colnames
        if headers=='fieldname:capitalize':
            headers = {}
            for c in columns:
                headers[c] = c.title() #c.split('.')[-1].replace('_',' ').title()
        elif headers=='labels':
            headers = {}
            for c in columns:
                (t,f) = c.split('.')
                try:
                    field = sqlrows.db[t][f]
                    headers[c] = field.label
                except:
                    headers[c] = c
                    
        if headers is None:
            headers = {}
        else:
            for c in columns:#new implement dict
                if isinstance(headers.get(c, c), dict):
                    coldict = headers.get(c, c)
                    attrcol = dict()
                    if coldict.has_key('width'):
                        attrcol.update(_width=coldict['width'])
                    if coldict.has_key('class'):
                        attrcol.update(_class=coldict['class'])  
                    if orderby:
                        if self.next_orderby.split('~')[-1] == c:
                            u = self.next_orderby
                        else:
                            u = c
                        _href = th_link+'?orderby=' + u
                        row.append(TH(A(coldict['label'], _href=_href),**attrcol))                        
                    else:
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
        if isinstance(sqlrows, Rows):
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
                            and isinstance(record,Row) \
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
    
                tbody.append(TR(*row))        
        else:
            for r in sqlrows:
                row = []
                for v in r:
                    row.append(TD(v))
                tbody.append(TR(*row))        
                
            
        table.append(TBODY(*tbody))

        return DIV(table, _class='web2py_table')

    
    def render_paginate(self):
        """Paginate"""

        request = current.request

        paginator = UL()
        ui = self.ui

        if self.rows_per_page < self.rows_count:
            npages, reminder = divmod(self.rows_count, self.rows_per_page)
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
    def render_search(search_action='list'):
        """search"""

        request = current.request
        
        label = LABEL('Search: ')
        search = INPUT(_type='text', value="", _placeholder="Search", _class="search-query", _onkeyup='getData(this.value);')

        script = SCRIPT("""function getData(value){
        $.get("%(url)s",{search_string:value},function(result){
        $("#%(grid_id)s").html($(result).contents()); 
        });
    }""" % {'url':URL(r=request,f=search_action, extension='load'), 'grid_id': 'grid_' + search_action})

        return FORM(script, label, search, _class='form-search') 

    