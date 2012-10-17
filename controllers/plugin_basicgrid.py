# -*- coding: utf-8 -*-
from gluon.contrib.populate import populate
db = DAL('sqlite:memory:')
db.define_table('product', 
    Field('name'),  Field('status', requires=IS_IN_SET(['new', 'old'])), 
    Field('description', 'text'),  
    Field('publish_start_date', 'date', label='start'), 
    Field('publish_end_date', 'date', label='end'),
    Field('price', 'integer', represent=lambda v: '$%s' % v ), 
    )
populate(db.product, 40)

#----------------------------------------------------------------------
def index():
    """"""
    return locals()

def grid():
    from plugin_basicgrid import BasicGrid
    basic_grid = BasicGrid(db, 
                           __file__.split('/')[-1][:-3], 
                           'grid', 
                           rows_per_page=10)
    helper = basic_grid.helper
    limit_inf = (basic_grid.rows_per_page * helper['page']) - basic_grid.rows_per_page
    limit_sup = limit_inf + basic_grid.rows_per_page
    query = (db.product.id > 0)
    query = query & (db.product.name.like('%' +  helper['search_string'] + '%'))

    basic_grid.rows_count = db(query).count()
    
    rows = db(query).select(orderby=helper['orderby'],limitby=(limit_inf, limit_sup))

    grid = basic_grid.table(rows, 
              columns=['product.id', 
                       'product.name', 
                       'product.description',
                       'product.publish_start_date',
                       'product.publish_end_date',
                       'product.price'],
              headers='labels',
              linkto=lambda r, mode, table: URL('show', args=[r]),
              cid='list_products'
              )

    return locals()

