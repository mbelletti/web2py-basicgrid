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
    search = Grid.render_search(search_action='grid')
    
    return locals()


def grid():
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
                ctrl=__file__.split('/')[-1][:-3], 
                method=request.function, 
                default_orderby=db.product.name,
                rows_per_page=10,
                cid = 'list_products')

    grid = DIV(grid.grid)

    return locals()

