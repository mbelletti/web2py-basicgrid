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
populate(db.product, 15)

#----------------------------------------------------------------------
def index():
    """
    Si appoggia a grid
    """
    from plugin_basicgrid import Grid
    # Passo a render_search 
    search = Grid.render_search()
    
    return locals()


def show():
    """"""
    rid = request.vars.get('avalue') or None
    record = db.product(rid)
    form = SQLFORM(db.product, record, readonly=True)
    return form


def list():
    from plugin_basicgrid import Grid
    
    query = None
    
    grid = Grid(db,
                fields=[db.product.id, 
                        db.product.name, 
                        db.product.description,
                        db.product.publish_start_date,
                        db.product.publish_end_date,
                        db.product.price],
                search_fields = [db.product.name, db.product.description],
                default_orderby=db.product.name,
                rows_for_page=10,
                show_function='show',
                search_function='list',                                
                cid = 'list_products')

    grid = DIV(grid.grid)

    return locals()


#----------------------------------------------------------------------
def grid():
    """"""
    from plugin_basicgrid import Grid
    
    query = None
    
    grid = Grid(db,
                fields=[db.product.id, 
                        db.product.name, 
                        db.product.description,
                        db.product.publish_start_date,
                        db.product.publish_end_date,
                        db.product.price],
                search_fields = [db.product.name, db.product.description],
                default_orderby=db.product.name,
                rows_for_page=10,
                cid = 'list_products')

    #grid = DIV(grid.grid)
    grid = grid()
    return locals()